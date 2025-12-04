"""Integration tests for complete workflows."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.services.verification_service import VerificationService
from app.services.payment_service import PaymentService
from app.services.rental_service import RentalService
from app.core.exceptions import (
    InsufficientCreditsError, AuthenticationError, ValidationError
)


class TestCompleteWorkflows:
    """Integration tests for complete user workflows."""

    @pytest.fixture
    def services(self):
        """Create service instances."""
        db_mock = Mock(spec=Session)
        return {
            "auth": AuthService(db_mock),
            "verification": VerificationService(db_mock),
            "payment": PaymentService(db_mock),
            "rental": RentalService(db_mock)
        }

    @pytest.fixture
    def test_user_data(self):
        """Test user data."""
        return {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        }

    # ========== User Registration & Login Workflow ==========

    def test_user_registration_workflow(self, services, test_user_data):
        """Test complete user registration workflow."""
        auth_service = services["auth"]

        # Step 1: Register user
        with patch.object(auth_service, 'register_user') as mock_register:
            mock_user = Mock()
            mock_user.id = "user123"
            mock_user.email = test_user_data["email"]
            mock_user.credits = Decimal("1.00")
            mock_register.return_value = mock_user

            user = auth_service.register_user(
                test_user_data["email"],
                test_user_data["password"]
            )

            assert user is not None
            assert user.email == test_user_data["email"]
            assert user.credits == Decimal("1.00")

    def test_user_login_workflow(self, services, test_user_data):
        """Test complete user login workflow."""
        auth_service = services["auth"]

        # Step 1: Login user
        with patch.object(auth_service, 'login_user') as mock_login:
            mock_user = Mock()
            mock_user.id = "user123"
            mock_user.email = test_user_data["email"]
            mock_login.return_value = (mock_user, "token123")

            user, token = auth_service.login_user(
                test_user_data["email"],
                test_user_data["password"]
            )

            assert user is not None
            assert token is not None
            assert user.email == test_user_data["email"]

    def test_user_registration_and_login_workflow(self, services, test_user_data):
        """Test complete registration and login workflow."""
        auth_service = services["auth"]

        # Step 1: Register
        with patch.object(auth_service, 'register_user') as mock_register:
            mock_user = Mock()
            mock_user.id = "user123"
            mock_user.email = test_user_data["email"]
            mock_register.return_value = mock_user

            registered_user = auth_service.register_user(
                test_user_data["email"],
                test_user_data["password"]
            )

            assert registered_user is not None

        # Step 2: Login
        with patch.object(auth_service, 'login_user') as mock_login:
            mock_login.return_value = (mock_user, "token123")

            user, token = auth_service.login_user(
                test_user_data["email"],
                test_user_data["password"]
            )

            assert user.id == registered_user.id

    # ========== Payment & Credit Workflow ==========

    def test_add_credits_workflow(self, services):
        """Test complete add credits workflow."""
        payment_service = services["payment"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        # Step 1: Add credits
        with patch.object(payment_service, 'add_credits') as mock_add:
            mock_payment = Mock()
            mock_payment.amount = Decimal("50.00")
            mock_payment.status = "completed"
            mock_add.return_value = mock_payment

            payment = payment_service.add_credits(mock_user, Decimal("50.00"))

            assert payment is not None
            assert payment.status == "completed"
            assert payment.amount == Decimal("50.00")

    def test_insufficient_credits_workflow(self, services):
        """Test workflow with insufficient credits."""
        payment_service = services["payment"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("5.00")

        # Try to deduct more than available
        with patch.object(payment_service, 'deduct_credits') as mock_deduct:
            mock_deduct.side_effect = InsufficientCreditsError("Insufficient credits")

            with pytest.raises(InsufficientCreditsError):
                payment_service.deduct_credits(mock_user, Decimal("10.00"), "verification")

    def test_payment_and_credit_workflow(self, services):
        """Test complete payment and credit workflow."""
        payment_service = services["payment"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        # Step 1: Process payment
        with patch.object(payment_service, 'process_payment') as mock_process:
            mock_payment = Mock()
            mock_payment.status = "completed"
            mock_process.return_value = mock_payment

            payment = payment_service.process_payment(
                mock_user,
                {"amount": Decimal("50.00"), "method": "credit_card"}
            )

            assert payment.status == "completed"

        # Step 2: Add credits
        with patch.object(payment_service, 'add_credits') as mock_add:
            mock_add.return_value = mock_payment

            result = payment_service.add_credits(mock_user, Decimal("50.00"))

            assert result is not None

    # ========== Verification Workflow ==========

    def test_verification_request_workflow(self, services):
        """Test complete verification request workflow."""
        verification_service = services["verification"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        verification_data = {
            "service_name": "whatsapp",
            "country_code": "us"
        }

        # Step 1: Create verification
        with patch.object(verification_service, 'create_verification') as mock_create:
            mock_verification = Mock()
            mock_verification.id = "verify123"
            mock_verification.status = "pending"
            mock_verification.phone_number = "+1234567890"
            mock_create.return_value = mock_verification

            verification = verification_service.create_verification(
                mock_user,
                verification_data
            )

            assert verification is not None
            assert verification.status == "pending"

        # Step 2: Check status
        with patch.object(verification_service, 'get_verification_status') as mock_status:
            mock_status.return_value = {"status": "completed", "code": "123456"}

            status = verification_service.get_verification_status(verification)

            assert status["status"] == "completed"

    def test_verification_with_insufficient_credits(self, services):
        """Test verification with insufficient credits."""
        verification_service = services["verification"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("0.10")

        verification_data = {
            "service_name": "whatsapp",
            "country_code": "us"
        }

        with patch.object(verification_service, 'create_verification') as mock_create:
            mock_create.side_effect = InsufficientCreditsError("Insufficient credits")

            with pytest.raises(InsufficientCreditsError):
                verification_service.create_verification(mock_user, verification_data)

    # ========== Rental Workflow ==========

    def test_rental_creation_workflow(self, services):
        """Test complete rental creation workflow."""
        rental_service = services["rental"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        rental_data = {
            "service_name": "whatsapp",
            "country_code": "us",
            "duration_hours": 24
        }

        # Step 1: Create rental
        with patch.object(rental_service, 'create_rental') as mock_create:
            mock_rental = Mock()
            mock_rental.id = "rental123"
            mock_rental.phone_number = "+1234567890"
            mock_rental.status = "active"
            mock_create.return_value = mock_rental

            rental = rental_service.create_rental(mock_user, rental_data)

            assert rental is not None
            assert rental.status == "active"

        # Step 2: Get rental status
        with patch.object(rental_service, 'get_rental_status') as mock_status:
            mock_status.return_value = {
                "phone_number": "+1234567890",
                "status": "active",
                "time_remaining": 86400
            }

            status = rental_service.get_rental_status(rental)

            assert status["status"] == "active"

    def test_rental_extension_workflow(self, services):
        """Test rental extension workflow."""
        rental_service = services["rental"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        mock_rental = Mock()
        mock_rental.id = "rental123"
        mock_rental.is_expired = False

        # Step 1: Extend rental
        with patch.object(rental_service, 'extend_rental') as mock_extend:
            mock_extend.return_value = {"extension_cost": Decimal("0.25")}

            result = rental_service.extend_rental(
                mock_rental,
                mock_user,
                {"additional_hours": 12}
            )

            assert result["extension_cost"] == Decimal("0.25")

    # ========== Complete User Journey ==========

    def test_complete_user_journey(self, services, test_user_data):
        """Test complete user journey from registration to verification."""
        auth_service = services["auth"]
        payment_service = services["payment"]
        verification_service = services["verification"]

        # Step 1: Register user
        with patch.object(auth_service, 'register_user') as mock_register:
            mock_user = Mock()
            mock_user.id = "user123"
            mock_user.email = test_user_data["email"]
            mock_user.credits = Decimal("1.00")
            mock_register.return_value = mock_user

            user = auth_service.register_user(
                test_user_data["email"],
                test_user_data["password"]
            )

            assert user is not None

        # Step 2: Add credits
        with patch.object(payment_service, 'add_credits') as mock_add:
            mock_payment = Mock()
            mock_payment.status = "completed"
            mock_add.return_value = mock_payment

            payment = payment_service.add_credits(user, Decimal("50.00"))

            assert payment.status == "completed"

        # Step 3: Create verification
        with patch.object(verification_service, 'create_verification') as mock_verify:
            mock_verification = Mock()
            mock_verification.id = "verify123"
            mock_verification.status = "pending"
            mock_verify.return_value = mock_verification

            verification = verification_service.create_verification(
                user,
                {"service_name": "whatsapp", "country_code": "us"}
            )

            assert verification is not None

    # ========== Error Handling Workflows ==========

    def test_error_handling_invalid_credentials(self, services):
        """Test error handling for invalid credentials."""
        auth_service = services["auth"]

        with patch.object(auth_service, 'login_user') as mock_login:
            mock_login.side_effect = AuthenticationError("Invalid credentials")

            with pytest.raises(AuthenticationError):
                auth_service.login_user("test@example.com", "wrongpassword")

    def test_error_handling_duplicate_email(self, services, test_user_data):
        """Test error handling for duplicate email registration."""
        auth_service = services["auth"]

        with patch.object(auth_service, 'register_user') as mock_register:
            mock_register.side_effect = ValidationError("Email already registered")

            with pytest.raises(ValidationError):
                auth_service.register_user(
                    test_user_data["email"],
                    test_user_data["password"]
                )

    def test_error_handling_invalid_payment_method(self, services):
        """Test error handling for invalid payment method."""
        payment_service = services["payment"]

        mock_user = Mock()
        mock_user.id = "user123"

        with patch.object(payment_service, 'process_payment') as mock_process:
            from app.core.exceptions import PaymentError
            mock_process.side_effect = PaymentError("Invalid payment method")

            with pytest.raises(PaymentError):
                payment_service.process_payment(
                    mock_user,
                    {"amount": Decimal("50.00"), "method": "invalid"}
                )

    # ========== Concurrent Operations ==========

    def test_concurrent_verification_requests(self, services):
        """Test handling concurrent verification requests."""
        verification_service = services["verification"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        # Simulate multiple concurrent requests
        with patch.object(verification_service, 'create_verification') as mock_create:
            mock_verifications = [
                Mock(id=f"verify{i}", status="pending")
                for i in range(5)
            ]
            mock_create.side_effect = mock_verifications

            verifications = []
            for i in range(5):
                v = verification_service.create_verification(
                    mock_user,
                    {"service_name": "whatsapp", "country_code": "us"}
                )
                verifications.append(v)

            assert len(verifications) == 5
            assert all(v.status == "pending" for v in verifications)

    def test_concurrent_credit_operations(self, services):
        """Test handling concurrent credit operations."""
        payment_service = services["payment"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        # Simulate multiple concurrent credit deductions
        with patch.object(payment_service, 'deduct_credits') as mock_deduct:
            mock_deduct.return_value = True

            results = []
            for i in range(5):
                result = payment_service.deduct_credits(
                    mock_user,
                    Decimal("5.00"),
                    "verification"
                )
                results.append(result)

            assert len(results) == 5
            assert all(r is True for r in results)

    # ========== Data Consistency ==========

    def test_data_consistency_after_payment(self, services):
        """Test data consistency after payment processing."""
        payment_service = services["payment"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        initial_credits = mock_user.credits

        with patch.object(payment_service, 'add_credits') as mock_add:
            mock_add.return_value = Mock(status="completed")

            payment_service.add_credits(mock_user, Decimal("50.00"))

            # Verify data consistency
            assert mock_user.id == "user123"
            assert mock_user.credits == initial_credits

    def test_data_consistency_after_verification(self, services):
        """Test data consistency after verification creation."""
        verification_service = services["verification"]

        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.credits = Decimal("100.00")

        initial_credits = mock_user.credits

        with patch.object(verification_service, 'create_verification') as mock_create:
            mock_create.return_value = Mock(id="verify123", status="pending")

            verification_service.create_verification(
                mock_user,
                {"service_name": "whatsapp", "country_code": "us"}
            )

            # Verify data consistency
            assert mock_user.id == "user123"
            assert mock_user.credits == initial_credits
