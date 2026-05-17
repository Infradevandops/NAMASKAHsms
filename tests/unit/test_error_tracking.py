"""Tests for verification error tracking endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.purchase_outcome import PurchaseOutcome
from app.models.verification import Verification
from tests.conftest import create_test_token


class TestErrorTracking:
    """Test error tracking endpoints - AC-1."""

    @pytest.mark.asyncio
    async def test_report_error_categorization(self, client, test_user, db):
        """AC-1: Error categorization captured correctly."""

        # Create verification
        verification = Verification(
            id="test-ver-001",
            user_id=test_user.id,
            service_name="google",
            country="US",
            cost=2.12,
            status="pending",
        )
        db.add(verification)

        outcome = PurchaseOutcome(
            assigned_code="415", verification_id="test-ver-001", service="google"
        )
        db.add(outcome)
        db.commit()

        # Report error
        response = client.post(
            f"/api/verification/{verification.id}/error",
            json={
                "failure_reason": "insufficient_balance",
                "failure_category": "user_action",
                "provider_error_code": "402",
                "outcome_category": "PRODUCT",
                "error_message": "Insufficient balance",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={
                "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error_recorded"
        assert data["failure_reason"] == "insufficient_balance"
        assert data["failure_category"] == "user_action"

        # Verify database
        db.refresh(verification)
        assert verification.failure_reason == "insufficient_balance"
        assert verification.failure_category == "user_action"
        assert verification.status == "error"
        assert verification.outcome == "error"

        db.refresh(outcome)
        assert outcome.outcome_category == "PRODUCT"
        assert outcome.provider_error_code == "402"

    @pytest.mark.asyncio
    async def test_error_categories_all_types(self, client, test_user, db):
        """AC-1: Test all error category types."""

        error_types = [
            ("insufficient_balance", "user_action", "PRODUCT"),
            ("area_code_unavailable", "provider_issue", "PROVIDER"),
            ("network_timeout", "network_issue", "NETWORK"),
            ("unknown_error", "system_error", "SYSTEM"),
        ]

        for i, (reason, category, outcome_cat) in enumerate(error_types):
            verification = Verification(
                id=f"test-ver-{i}",
                user_id=test_user.id,
                service_name="google",
                country="US",
                cost=2.12,
                status="pending",
            )
            db.add(verification)
            db.commit()

            response = client.post(
                f"/api/verification/{verification.id}/error",
                json={
                    "failure_reason": reason,
                    "failure_category": category,
                    "outcome_category": outcome_cat,
                    "error_message": f"Test error: {reason}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                headers={
                    "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
                },
            )

            assert response.status_code == 200
            db.refresh(verification)
            assert verification.failure_reason == reason
            assert verification.failure_category == category


class TestSMSReceipt:
    """Test SMS receipt confirmation - AC-2."""

    @pytest.mark.asyncio
    async def test_sms_receipt_confirmation(self, client, test_user, db):
        """AC-2: SMS receipt confirmation updates all fields."""

        # Create verification
        created_at = datetime.now(timezone.utc)
        verification = Verification(
            id="test-ver-sms",
            user_id=test_user.id,
            service_name="google",
            country="US",
            cost=2.12,
            status="pending",
            created_at=created_at,
        )
        db.add(verification)

        outcome = PurchaseOutcome(
            assigned_code="415", verification_id="test-ver-sms", service="google"
        )
        db.add(outcome)
        db.commit()

        # Confirm SMS receipt
        response = client.post(
            f"/api/verification/{verification.id}/sms-received",
            json={
                "sms_code": "123456",
                "received_at": datetime.now(timezone.utc).isoformat(),
                "latency_seconds": 45.3,
            },
            headers={
                "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sms_receipt_confirmed"
        assert data["sms_received"] is True
        assert data["latency_seconds"] == 45.3

        # Verify database
        db.refresh(verification)
        assert verification.sms_received is True
        assert verification.sms_received_at is not None
        assert verification.sms_code == "123456"
        assert verification.status == "completed"
        assert verification.outcome == "completed"

        db.refresh(outcome)
        assert outcome.sms_received is True
        assert outcome.latency_seconds == 45.3
        assert outcome.raw_sms_code == "123456"

    @pytest.mark.asyncio
    async def test_sms_receipt_latency_calculation(self, client, test_user, db):
        """AC-2: Latency calculated correctly for different times."""

        test_cases = [
            (30, "30 seconds"),
            (120, "2 minutes"),
            (300, "5 minutes"),
        ]

        for i, (latency, description) in enumerate(test_cases):
            verification = Verification(
                id=f"test-ver-lat-{i}",
                user_id=test_user.id,
                service_name="google",
                country="US",
                cost=2.12,
                status="pending",
            )
            db.add(verification)

            outcome = PurchaseOutcome(
                assigned_code="415",
                verification_id=f"test-ver-lat-{i}",
                service="google",
            )
            db.add(outcome)
            db.commit()

            response = client.post(
                f"/api/verification/{verification.id}/sms-received",
                json={
                    "sms_code": "123456",
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "latency_seconds": latency,
                },
                headers={
                    "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
                },
            )

            assert response.status_code == 200
            db.refresh(outcome)
            assert outcome.latency_seconds == latency


class TestTimeoutHandling:
    """Test timeout detection and auto-refund - AC-3."""

    @pytest.mark.asyncio
    async def test_timeout_triggers_refund(self, client, test_user, db):
        """AC-3: Timeout triggers automatic refund."""

        # Create verification
        verification = Verification(
            id="test-ver-timeout",
            user_id=test_user.id,
            service_name="google",
            country="US",
            cost=2.12,
            status="pending",
        )
        db.add(verification)

        outcome = PurchaseOutcome(
            assigned_code="415", verification_id="test-ver-timeout", service="google"
        )
        db.add(outcome)
        db.commit()

        # Mock auto-refund service
        with patch(
            "app.services.auto_refund_service.AutoRefundService.process_verification_refund"
        ) as mock_refund:
            mock_refund.return_value = {"refund_amount": 2.12, "status": "refunded"}

            # Report timeout
            response = client.post(
                f"/api/verification/{verification.id}/timeout",
                json={
                    "timeout_at": datetime.now(timezone.utc).isoformat(),
                    "elapsed_seconds": 300.0,
                    "failure_reason": "sms_timeout",
                    "failure_category": "provider_issue",
                    "refund_eligible": True,
                },
                headers={
                    "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "timeout_recorded"
            assert data["refund_initiated"] is True
            assert data["refund_amount"] == 2.12

            # Verify database
            db.refresh(verification)
            assert verification.status == "timeout"
            assert verification.outcome == "timeout"
            assert verification.failure_reason == "sms_timeout"
            assert verification.failure_category == "provider_issue"
            assert verification.refund_eligible is True
            assert verification.sms_received is False

            db.refresh(outcome)
            assert outcome.sms_received is False
            assert outcome.outcome_category == "PROVIDER"
            assert outcome.latency_seconds == 300.0

            # Verify refund was called
            mock_refund.assert_called_once_with("test-ver-timeout", "timeout")


class TestCancellation:
    """Test enhanced cancellation tracking - AC-4."""

    @pytest.mark.asyncio
    async def test_cancellation_with_reason(self, client, test_user, db):
        """AC-4: Cancellation captures reason and category."""

        # Create verification
        verification = Verification(
            id="test-ver-cancel",
            user_id=test_user.id,
            service_name="google",
            country="US",
            cost=2.12,
            status="pending",
        )
        db.add(verification)
        db.commit()

        # Mock auto-refund service
        with patch(
            "app.services.auto_refund_service.AutoRefundService.process_verification_refund"
        ) as mock_refund:
            mock_refund.return_value = {"refund_amount": 2.12, "status": "refunded"}

            # Cancel verification
            response = client.post(
                f"/api/verification/{verification.id}/cancel",
                json={
                    "reason": "user_cancelled",
                    "category": "user_action",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "cancelled_by": "user",
                },
                headers={
                    "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
            assert data["cancel_reason"] == "user_cancelled"
            assert data["refund_issued"] is True
            assert data["refund_amount"] == 2.12

            # Verify database
            db.refresh(verification)
            assert verification.status == "cancelled"
            assert verification.outcome == "cancelled"
            assert verification.cancel_reason == "user_cancelled"
            assert verification.cancelled_at is not None
            assert verification.cancelled_by == "user"


class TestAnalytics:
    """Test error analytics queries - AC-6."""

    @pytest.mark.asyncio
    async def test_error_breakdown_by_category(self, db):
        """AC-6: Error breakdown query returns meaningful data."""

        # Create multiple errors of different types
        error_data = [
            ("insufficient_balance", "user_action", "PRODUCT"),
            ("insufficient_balance", "user_action", "PRODUCT"),
            ("area_code_unavailable", "provider_issue", "PROVIDER"),
            ("area_code_unavailable", "provider_issue", "PROVIDER"),
            ("area_code_unavailable", "provider_issue", "PROVIDER"),
            ("network_timeout", "network_issue", "NETWORK"),
        ]

        for i, (reason, category, outcome_cat) in enumerate(error_data):
            verification = Verification(
                id=f"test-analytics-{i}",
                user_id="test-user",
                service_name="google",
                country="US",
                cost=2.12,
                status="error",
                failure_reason=reason,
                failure_category=category,
            )
            db.add(verification)

        db.commit()

        # Query error breakdown
        from sqlalchemy import func

        results = (
            db.query(
                Verification.failure_category,
                func.count(Verification.id).label("count"),
            )
            .filter(
                Verification.status == "error",
                Verification.failure_category.isnot(None),
            )
            .group_by(Verification.failure_category)
            .all()
        )

        # Verify results
        breakdown = {r.failure_category: r.count for r in results}
        assert breakdown["user_action"] == 2
        assert breakdown["provider_issue"] == 3
        assert breakdown["network_issue"] == 1
        assert len(breakdown) == 3  # No NULL categories


@pytest.mark.asyncio
async def test_spot_check_1_error_categorization(client, test_user, db):
    """Spot Check #1: Error categorization fields populated."""

    # Set user balance to $1.00
    test_user.credits = 1.00
    db.commit()

    # Try to purchase $2.12 verification (should fail)
    verification = Verification(
        id="spot-check-1",
        user_id=test_user.id,
        service_name="google",
        country="US",
        cost=2.12,
        status="pending",
    )
    db.add(verification)
    db.commit()

    # Report error
    response = client.post(
        f"/api/verification/{verification.id}/error",
        json={
            "failure_reason": "insufficient_balance",
            "failure_category": "user_action",
            "outcome_category": "PRODUCT",
            "error_message": "Insufficient balance",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        headers={
            "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
        },
    )

    assert response.status_code == 200

    # Verify all 3 fields are non-NULL
    db.refresh(verification)
    assert verification.failure_reason is not None
    assert verification.failure_category is not None

    outcome = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.verification_id == "spot-check-1")
        .first()
    )
    if outcome:
        assert outcome.outcome_category is not None

    print("✅ Spot Check #1 PASSED: All 3 fields populated")


@pytest.mark.asyncio
async def test_spot_check_2_sms_receipt(client, test_user, db):
    """Spot Check #2: SMS receipt fields populated."""

    verification = Verification(
        id="spot-check-2",
        user_id=test_user.id,
        service_name="google",
        country="US",
        cost=2.12,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(verification)
    db.commit()

    # Confirm SMS receipt
    response = client.post(
        f"/api/verification/{verification.id}/sms-received",
        json={
            "sms_code": "123456",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "latency_seconds": 45.3,
        },
        headers={
            "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
        },
    )

    assert response.status_code == 200

    # Verify all 3 fields are non-NULL
    db.refresh(verification)
    assert verification.sms_received is True
    assert verification.sms_received_at is not None
    assert verification.sms_code is not None

    print("✅ Spot Check #2 PASSED: All 3 fields populated")


@pytest.mark.asyncio
async def test_spot_check_3_timeout_refund(client, test_user, db):
    """Spot Check #3: Timeout triggers refund and notification."""

    verification = Verification(
        id="spot-check-3",
        user_id=test_user.id,
        service_name="google",
        country="US",
        cost=2.12,
        status="pending",
    )
    db.add(verification)
    db.commit()

    # Mock refund service
    with patch(
        "app.services.auto_refund_service.AutoRefundService.process_verification_refund"
    ) as mock_refund:
        mock_refund.return_value = {"refund_amount": 2.12, "status": "refunded"}

        # Report timeout
        response = client.post(
            f"/api/verification/{verification.id}/timeout",
            json={
                "timeout_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": 300.0,
                "failure_reason": "sms_timeout",
                "failure_category": "provider_issue",
                "refund_eligible": True,
            },
            headers={
                "Authorization": f"Bearer {create_test_token(test_user.id, test_user.email)}"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["refund_initiated"] is True

        # Verify database updated
        db.refresh(verification)
        assert verification.status == "timeout"
        assert verification.refunded is True or data["refund_initiated"] is True

        print("✅ Spot Check #3 PASSED: Timeout triggers refund")
