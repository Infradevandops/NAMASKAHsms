import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from app.services.payment_service import PaymentService
from app.models.transaction import PaymentLog, Transaction

class TestPaymentService:
    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    @patch("app.services.payment_service.paystack_service")
    async def test_initiate_payment_success(self, mock_paystack, payment_service, regular_user, db_session):
        # Setup mock
        mock_paystack.enabled = True
        mock_paystack.initialize_payment = AsyncMock(return_value={
            "authorization_url": "https://checkout.paystack.com/auth",
            "access_code": "test_access_code"
        })
        
        amount_usd = 10.0
        result = await payment_service.initiate_payment(regular_user.id, amount_usd)
        
        assert result["amount_usd"] == amount_usd
        assert result["status"] == "pending"
        assert "reference" in result
        
        # Verify PaymentLog created
        log = db_session.query(PaymentLog).filter(PaymentLog.reference == result["reference"]).first()
        assert log is not None
        assert log.user_id == regular_user.id
        assert log.amount_usd == amount_usd
        assert log.status == "pending"

    async def test_initiate_payment_invalid_amount(self, payment_service, regular_user):
        with pytest.raises(ValueError, match="Amount must be positive"):
            await payment_service.initiate_payment(regular_user.id, -5.0)

    @patch("app.services.payment_service.paystack_service")
    async def test_verify_payment_success(self, mock_paystack, payment_service, regular_user, db_session):
        # 1. Setup a pending payment log
        reference = "ref_123"
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference=reference,
            amount_usd=10.0,
            amount_ngn=15000.0,
            namaskah_amount=10.0,
            status="pending",
            credited=False
        )
        db_session.add(log)
        db_session.commit()
        
        # 2. Mock Paystack verification
        mock_paystack.verify_payment = AsyncMock(return_value={
            "status": "success",
            "paid_at": datetime.now(timezone.utc).isoformat()
        })
        
        # 3. Verify
        result = await payment_service.verify_payment(reference, regular_user.id)
        
        assert result["status"] == "success"
        assert result["credited"] is True
        
        # 4. Check DB updates
        db_session.refresh(log)
        assert log.status == "success"
        assert log.credited is True
        
        db_session.refresh(regular_user)
        assert regular_user.credits == 10.0  # Assumes 0 initial

    def test_handle_charge_success_webhook(self, payment_service, regular_user, db_session):
        # 1. Setup pending payment
        reference = "ref_webhook"
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference=reference,
            amount_usd=20.0,
            amount_ngn=30000.0,
            namaskah_amount=20.0,
            status="pending",
            credited=False
        )
        db_session.add(log)
        db_session.commit()
        
        payload = {"reference": reference, "amount": 3000000} # 30000 NGN in kobo
        
        # 2. Process webhook
        result = payment_service.process_webhook("charge.success", payload)
        
        assert result["status"] == "success"
        
        # 3. Check DB
        db_session.refresh(log)
        assert log.status == "success"
        assert log.credited is True
        
        db_session.refresh(regular_user)
        assert regular_user.credits == 20.0

    def test_handle_charge_failed_webhook(self, payment_service, regular_user, db_session):
        reference = "ref_fail"
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference=reference,
            amount_usd=5.0,
            status="pending"
        )
        db_session.add(log)
        db_session.commit()
        
        payment_service.process_webhook("charge.failed", {"reference": reference})
        
        db_session.refresh(log)
        assert log.status == "failed"
        assert log.webhook_received is True
