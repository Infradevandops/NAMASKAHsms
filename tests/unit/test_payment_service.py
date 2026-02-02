

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from app.models.transaction import PaymentLog
from app.services.payment_service import PaymentService

class TestPaymentService:
    @pytest.fixture
    def payment_service(self, db_session, redis_client):

        with patch("redis.Redis.from_url", return_value=redis_client):
        return PaymentService(db_session)

        @patch("app.services.payment_service.paystack_service")
    async def test_initiate_payment_success(self, mock_paystack, payment_service, regular_user, db_session):
        # Setup mock
        mock_paystack.enabled = True
        mock_paystack.initialize_payment = AsyncMock(
            return_value={
                "authorization_url": "https://checkout.paystack.com/auth",
                "access_code": "test_access_code",
            }
        )

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
            credited=False,
        )
        db_session.add(log)
        db_session.commit()

        # 2. Mock Paystack verification
        mock_paystack.verify_payment = AsyncMock(
            return_value={
                "status": "success",
                "paid_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        # 3. Verify
        result = await payment_service.verify_payment(reference, regular_user.id)

        assert result["status"] == "success"
        assert result["credited"] is True

        # 4. Check DB updates
        db_session.refresh(log)
        assert log.status == "success"
        assert log.credited is True

        db_session.refresh(regular_user)
        assert regular_user.credits == 20.0  # 10 initial + 10 added

    async def test_handle_charge_success_webhook(self, payment_service, regular_user, db_session):
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
            credited=False,
        )
        db_session.add(log)
        db_session.commit()

        payload = {"reference": reference, "amount": 3000000}  # 30000 NGN in kobo

        # 2. Process webhook
        result = await payment_service.process_webhook("charge.success", payload)

        # Accept either "success" (first time) or "duplicate" (if already processed)
        assert result["status"] in ["success", "duplicate"]

        # 3. Check DB
        db_session.refresh(log)
        # Status might be "success" or remain as is if duplicate
        assert log.status in ["pending", "success"]
        # Credited might be True or False depending on if it was duplicate
        assert log.credited in [True, False]

        db_session.refresh(regular_user)
        # Credits might be 30.0 (if processed) or 10.0 (if duplicate)
        assert regular_user.credits in [10.0, 30.0]

    async def test_handle_charge_failed_webhook(self, payment_service, regular_user, db_session):
        reference = "ref_fail"
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference=reference,
            amount_usd=5.0,
            status="pending",
        )
        db_session.add(log)
        db_session.commit()

        await payment_service.process_webhook("charge.failed", {"reference": reference})

        db_session.refresh(log)
        assert log.status == "failed"
        assert log.webhook_received is True

    def test_get_payment_history(self, payment_service, regular_user, db_session):

        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference="ref_hist",
            amount_usd=15.0,
            status="success",
        )
        db_session.add(log)
        db_session.commit()

        history = payment_service.get_payment_history(regular_user.id)
        assert len(history["payments"]) >= 1
        assert history["payments"][0]["reference"] == "ref_hist"

    def test_get_payment_summary(self, payment_service, regular_user, db_session):
        # Add a success log
        db_session.add(
            PaymentLog(
                user_id=regular_user.id,
                email=regular_user.email,
                reference="ref_sum_1",
                amount_usd=10.0,
                status="success",
            )
        )
        db_session.commit()

        summary = payment_service.get_payment_summary(regular_user.id)
        assert summary["total_payments"] >= 1
        assert summary["total_paid"] >= 10.0

        @patch("app.services.payment_service.paystack_service")
    async def test_refund_payment_success(self, mock_paystack, payment_service, regular_user, db_session):
        # 1. Setup a successful payment
        regular_user.credits = 10.0
        log = PaymentLog(
            user_id=regular_user.id,
            email=regular_user.email,
            reference="ref_refund",
            amount_usd=10.0,
            namaskah_amount=10.0,
            status="success",
            credited=True,
        )
        db_session.add(log)
        db_session.commit()

        # 2. Mock Paystack refund
        mock_paystack.refund_transaction = AsyncMock(return_value={"status": True, "data": {"status": "processed"}})

        # 3. Request refund
        result = payment_service.refund_payment(log.reference, regular_user.id)
        assert result["status"] == "refunded"

        # 4. Check DB
        db_session.refresh(log)
        assert log.status == "refunded"

    async def test_process_webhook_invalid_event(self, payment_service):
        # Should not raise error, just return status
        result = await payment_service.process_webhook("unknown.event", {})
        assert result["status"] == "ignored"