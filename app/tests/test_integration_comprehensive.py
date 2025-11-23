"""Comprehensive integration tests for external services and complex workflows."""
from unittest.mock import patch, Mock, AsyncMock

from app.services.payment_service import PaymentService


class TestDatabaseTransactionHandling:
    """Test database operations and transaction handling."""

    def test_transaction_rollback_on_error(self, db_session, test_user):
        """Test that database transactions rollback on errors."""
        initial_credits = test_user.credits

        try:
            test_user.credits += 10.0
            db_session.add(test_user)

            # Create invalid transaction (missing required field)
            transaction = Transaction(
                user_id=test_user.id,
                amount=10.0,
                type="credit"
                # Missing description - should cause error
            )
            db_session.add(transaction)
            db_session.commit()
        except Exception:
            db_session.rollback()

        # Verify rollback occurred
        db_session.refresh(test_user)
        assert test_user.credits == initial_credits

    def test_concurrent_user_updates(self, db_session):
        """Test handling of concurrent user updates."""
        user = User(
            id="concurrent_test",
            email="concurrent@test.com",
            password_hash="hash",
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()


class TestPaymentServiceIntegration:
    """Test payment service integration with external APIs."""

    @patch('httpx.AsyncClient.get')
    async def test_exchange_rate_fetch_success(self, mock_get, db_session):
        """Test successful exchange rate fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rates": {"NGN": 1500.0}}
        mock_get.return_value = mock_response

        payment_service = PaymentService(db_session)
        rate = await payment_service._get_exchange_rate()

        assert rate == 1500.0
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.post')
    async def test_paystack_initialization_success(self, mock_post,
                                                   db_session, test_user):
        """Test successful Paystack payment initialization."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "authorization_url": "https://checkout.paystack.com/test",
                "access_code": "test_access_code",
                "reference": "test_ref_123"
            }
        }
        mock_post.return_value = mock_response

        payment_service = PaymentService(db_session)

        with patch.object(payment_service, '_get_exchange_rate', return_value=1500.0):
            result = await payment_service.initialize_payment(
                user_id=test_user.id,
                email=test_user.email,
                amount_usd=10.0
            )

        assert result["success"] is True
        assert "authorization_url" in result
        assert "reference" in result

        # Verify payment log was created
        payment_log = db_session.query(PaymentLog).filter(
            PaymentLog.user_id == test_user.id
        ).first()
        assert payment_log is not None
        assert payment_log.status == "initialized"

    def test_webhook_signature_verification(self, db_session):
        """Test Paystack webhook signature verification."""
        payment_service = PaymentService(db_session)

        # Mock secret key
        with patch.object(payment_service, 'secret_key', 'test_secret'):
            payload = b'{"event": "charge.success"}'

            # Generate valid signature
            import hashlib
            import hmac
            valid_signature = hmac.new(
                b'test_secret',
                payload,
                hashlib.sha512
            ).hexdigest()

            # Test valid signature
            assert payment_service.verify_webhook_signature(payload, valid_signature) is True

            # Test invalid signature
            assert payment_service.verify_webhook_signature(payload, "invalid") is False

    def test_webhook_payment_processing(self, db_session, test_user):
        """Test webhook payment processing."""
        payment_service = PaymentService(db_session)

        webhook_data = {
            "event": "charge.success",
            "data": {
                "reference": "test_ref_123",
                "amount": 1500000,  # 15000 NGN in kobo
                "metadata": {
                    "user_id": test_user.id,
                    "namaskah_amount": 5.0
                }
            }
        }

        initial_credits = test_user.credits
        result = payment_service.process_webhook_payment(webhook_data)

        assert result is True

        # Verify credits were added
        db_session.refresh(test_user)
        assert test_user.credits == initial_credits + 5.0

        # Verify transaction was created
        transaction = db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.type == "credit"
        ).first()
        assert transaction is not None
        assert transaction.amount == 5.0


class TestNotificationServiceIntegration:
    """Test notification service integration."""

    @patch('smtplib.SMTP')
    async def test_email_sending_success(self, mock_smtp, db_session):
        """Test successful email sending."""
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        notification_service = NotificationService(db_session)

        with patch('app.services.notification_service.settings') as mock_settings:
            mock_settings.smtp_host = "smtp.gmail.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_user = "test@gmail.com"
            mock_settings.smtp_password = "password"
            mock_settings.from_email = "noreply@namaskah.app"

            result = await notification_service.send_email(
                to_email="user@example.com",
                subject="Test Email",
                body="Test message"
            )

            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@gmail.com", "password")
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_webhook_delivery_success(self, mock_client, db_session, test_user):
        """Test successful webhook delivery."""
        # Create test webhook
        webhook = Webhook(
            id="webhook_123",
            user_id=test_user.id,
            url="https://example.com/webhook",
            is_active=True
        )
        db_session.add(webhook)
        db_session.commit()

        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        notification_service = NotificationService(db_session)

        results = await notification_service.send_webhook(
            user_id=test_user.id,
            event_type="verification.completed",
            payload={"verification_id": "123"}
        )

        assert len(results) == 1
        assert results[0] is True
        mock_client_instance.post.assert_called_once()

    def test_in_app_notification_creation(self, db_session, test_user):
        """Test in - app notification creation and retrieval."""
        notification_service = NotificationService(db_session)

        # Create notification
        notification = notification_service.create_in_app_notification(
            user_id=test_user.id,
            title="Test Notification",
            message="This is a test message",
            notification_type="info"
        )

        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.title == "Test Notification"
        assert not notification.is_read

        # Retrieve notifications
        notifications = notification_service.get_user_notifications(test_user.id)
        assert len(notifications) == 1
        assert notifications[0]["title"] == "Test Notification"

        # Mark as read
        success = notification_service.mark_notification_read(notification.id, test_user.id)
        assert success is True

        # Verify marked as read
        updated_notifications = notification_service.get_user_notifications(
            test_user.id, unread_only=True
        )
        assert len(updated_notifications) == 0


class TestAuthenticationFlows:
    """Test authentication flows and security measures."""

    def test_complete_user_registration_flow(self, db_session):
        """Test complete user registration workflow."""
        auth_service = AuthService(db_session)

        # Register user
        user = auth_service.register_user(
            email="newuser@example.com",
            password="securepassword123"
        )

        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.password_hash != "securepassword123"  # Should be hashed
        assert user.referral_code is not None
        assert user.free_verifications == 1.0
        assert not user.email_verified

        # Authenticate user
        authenticated_user = auth_service.authenticate_user(
            "newuser@example.com",
            "securepassword123"
        )

        assert authenticated_user is not None
        assert authenticated_user.id == user.id

    def test_jwt_token_lifecycle(self, db_session, test_user):
        """Test JWT token creation, validation, and expiration."""
        auth_service = AuthService(db_session)

        # Create token
        token = auth_service.create_user_token(test_user)
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        payload = auth_service.verify_user_token(token)
        assert payload is not None
        assert payload["user_id"] == test_user.id
        assert payload["email"] == test_user.email

        # Get user from token
        retrieved_user = auth_service.get_user_from_token(token)
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id

        # Test invalid token
        invalid_user = auth_service.get_user_from_token("invalid_token")
        assert invalid_user is None

    def test_api_key_management_flow(self, db_session, test_user):
        """Test API key creation, verification, and management."""
        auth_service = AuthService(db_session)

        # Create API key
        api_key = auth_service.create_api_key(test_user.id, "Test API Key")
        assert api_key is not None
        assert api_key.user_id == test_user.id
        assert api_key.name == "Test API Key"
        assert api_key.key.startswith("nsk_")
        assert api_key.is_active is True

        # Verify API key
        verified_user = auth_service.verify_api_key(api_key.key)
        assert verified_user is not None
        assert verified_user.id == test_user.id

        # Deactivate API key
        success = auth_service.deactivate_api_key(api_key.id, test_user.id)
        assert success is True

        # Verify deactivated key doesn't work
        deactivated_user = auth_service.verify_api_key(api_key.key)
        assert deactivated_user is None

        # Get user API keys
        api_keys = auth_service.get_user_api_keys(test_user.id)
        assert len(api_keys) == 1
        assert not api_keys[0].is_active

    def test_admin_access_control(self, db_session, test_user, admin_user):
        """Test admin access control mechanisms."""
        auth_service = AuthService(db_session)

        # Regular user should not have admin access
        assert auth_service.verify_admin_access(test_user.id) is False

        # Admin user should have admin access
        assert auth_service.verify_admin_access(admin_user.id) is True

        # Test with non - existent user
        assert auth_service.verify_admin_access("nonexistent") is False
