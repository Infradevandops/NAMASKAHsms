"""Tests for TierManager and CreditService to boost coverage."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from app.core.exceptions import InsufficientCreditsError
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.credit_service import CreditService
from app.services.tier_manager import TierManager


# ── TierManager ──────────────────────────────────────────────────────


class TestGetUserTier:
    def test_returns_freemium_for_missing_user(self, db):
        tm = TierManager(db)
        assert tm.get_user_tier("nonexistent") == "freemium"

    def test_returns_stored_tier(self, db, test_user):
        test_user.subscription_tier = "payg"
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(test_user.id) == "payg"

    def test_admin_bypasses_expiry(self, db, admin_user):
        admin_user.subscription_tier = "custom"
        admin_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=30)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(admin_user.id) == "custom"

    def test_admin_defaults_to_custom_if_unknown(self, db, admin_user):
        admin_user.subscription_tier = "bogus"
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(admin_user.id) == "custom"

    def test_unknown_tier_falls_back_to_freemium(self, db, regular_user):
        regular_user.subscription_tier = "invalid_tier"
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(regular_user.id) == "freemium"

    def test_expired_pro_downgrades(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            credits=0,
            subscription_tier="pro",
            is_admin=False,
            tier_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "freemium"
        db.refresh(user)
        assert user.subscription_tier == "freemium"

    def test_non_expired_pro_stays(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            credits=0,
            subscription_tier="pro",
            is_admin=False,
            tier_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "pro"

    def test_payg_not_subject_to_expiry(self, db, payg_user):
        payg_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(payg_user.id) == "payg"

    def test_none_tier_defaults_freemium(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email=f"{uid[:8]}@test.com",
            password_hash="hash",
            credits=0,
            subscription_tier=None,
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        tm = TierManager(db)
        assert tm.get_user_tier(uid) == "freemium"


class TestCheckFeatureAccess:
    def test_pro_has_api_access(self, db, pro_user):
        tm = TierManager(db)
        assert tm.check_feature_access(pro_user.id, "api_access") is True

    def test_freemium_no_api_access(self, db, regular_user):
        tm = TierManager(db)
        assert tm.check_feature_access(regular_user.id, "api_access") is False

    def test_unknown_feature_returns_false(self, db, pro_user):
        tm = TierManager(db)
        assert tm.check_feature_access(pro_user.id, "nonexistent_feature") is False


class TestTierLimits:
    def test_returns_limits_dict(self, db, test_user):
        tm = TierManager(db)
        limits = tm.get_tier_limits(test_user.id)
        assert "daily_verification_limit" in limits
        assert "api_key_limit" in limits


class TestUpgradeDowngrade:
    def test_upgrade_user_tier(self, db, regular_user):
        tm = TierManager(db)
        assert tm.upgrade_user_tier(regular_user.id, "payg") is True
        db.refresh(regular_user)
        assert regular_user.subscription_tier == "payg"

    def test_upgrade_invalid_tier(self, db, regular_user):
        tm = TierManager(db)
        assert tm.upgrade_user_tier(regular_user.id, "platinum") is False

    def test_upgrade_nonexistent_user(self, db):
        tm = TierManager(db)
        assert tm.upgrade_user_tier("nope", "payg") is False

    def test_downgrade_user(self, db, pro_user):
        tm = TierManager(db)
        assert tm.downgrade_user_tier(pro_user.id, "manual") is True
        db.refresh(pro_user)
        assert pro_user.subscription_tier == "freemium"

    def test_downgrade_nonexistent_user(self, db):
        tm = TierManager(db)
        assert tm.downgrade_user_tier("nope") is False


class TestCheckTierHierarchy:
    def test_same_tier(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("payg", "payg") is True

    def test_higher_tier(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("pro", "payg") is True

    def test_lower_tier(self, db):
        tm = TierManager(db)
        assert tm.check_tier_hierarchy("freemium", "payg") is False


class TestCanCreateApiKey:
    def test_freemium_cannot(self, db, regular_user):
        tm = TierManager(db)
        ok, msg = tm.can_create_api_key(regular_user.id)
        assert ok is False
        assert "Pro tier" in msg or "requires" in msg.lower()

    def test_pro_can(self, db, pro_user):
        tm = TierManager(db)
        ok, _ = tm.can_create_api_key(pro_user.id)
        assert ok is True


class TestGetAllTiers:
    def test_returns_list(self, db):
        tm = TierManager(db)
        tiers = tm.get_all_tiers()
        assert isinstance(tiers, list)


# ── CreditService ────────────────────────────────────────────────────


class TestGetBalance:
    def test_returns_balance(self, db, test_user):
        svc = CreditService(db)
        bal = svc.get_balance(test_user.id)
        assert bal == float(test_user.credits)

    def test_missing_user_raises(self, db):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.get_balance("nonexistent")


class TestAddCredits:
    def test_adds_credits(self, db, regular_user):
        svc = CreditService(db)
        result = svc.add_credits(regular_user.id, 10.0, "test add")
        assert result["amount_added"] == 10.0
        assert result["new_balance"] > result["old_balance"]

    def test_zero_amount_raises(self, db, regular_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.add_credits(regular_user.id, 0)

    def test_negative_amount_raises(self, db, regular_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.add_credits(regular_user.id, -5)

    def test_missing_user_raises(self, db):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.add_credits("nonexistent", 10)


class TestDeductCredits:
    def test_deducts_credits(self, db, test_user):
        svc = CreditService(db)
        result = svc.deduct_credits(test_user.id, 5.0, "test deduct")
        assert result["amount_deducted"] == 5.0
        assert result["new_balance"] < result["old_balance"]

    def test_insufficient_credits_raises(self, db, regular_user):
        regular_user.credits = 1.0
        db.commit()
        svc = CreditService(db)
        with pytest.raises(InsufficientCreditsError):
            svc.deduct_credits(regular_user.id, 999.0)

    def test_zero_amount_raises(self, db, test_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.deduct_credits(test_user.id, 0)

    def test_missing_user_raises(self, db):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.deduct_credits("nonexistent", 5)


class TestTransactionHistory:
    def test_returns_history(self, db, test_user):
        svc = CreditService(db)
        svc.add_credits(test_user.id, 5.0, "hist test")
        result = svc.get_transaction_history(test_user.id)
        assert result["total"] >= 1
        assert len(result["transactions"]) >= 1

    def test_filter_by_type(self, db, test_user):
        svc = CreditService(db)
        result = svc.get_transaction_history(test_user.id, transaction_type="credit")
        for t in result["transactions"]:
            assert t["type"] == "credit"

    def test_pagination(self, db, test_user):
        svc = CreditService(db)
        result = svc.get_transaction_history(test_user.id, skip=0, limit=1)
        assert result["limit"] == 1

    def test_missing_user_raises(self, db):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.get_transaction_history("nonexistent")


class TestTransactionSummary:
    def test_returns_summary(self, db, test_user):
        svc = CreditService(db)
        summary = svc.get_transaction_summary(test_user.id)
        assert "current_balance" in summary
        assert "transaction_count" in summary

    def test_missing_user_raises(self, db):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.get_transaction_summary("nonexistent")


class TestTransferCredits:
    def test_transfer_succeeds(self, db):
        uid1, uid2 = str(uuid.uuid4()), str(uuid.uuid4())
        u1 = User(
            id=uid1,
            email=f"{uid1[:8]}@t.com",
            password_hash="h",
            credits=50.0,
            subscription_tier="payg",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        u2 = User(
            id=uid2,
            email=f"{uid2[:8]}@t.com",
            password_hash="h",
            credits=10.0,
            subscription_tier="payg",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([u1, u2])
        db.commit()
        svc = CreditService(db)
        result = svc.transfer_credits(uid1, uid2, 20.0)
        assert result["from_user_new_balance"] == 30.0
        assert result["to_user_new_balance"] == 30.0

    def test_transfer_insufficient_raises(self, db):
        uid1, uid2 = str(uuid.uuid4()), str(uuid.uuid4())
        u1 = User(
            id=uid1,
            email=f"{uid1[:8]}@t.com",
            password_hash="h",
            credits=5.0,
            subscription_tier="payg",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        u2 = User(
            id=uid2,
            email=f"{uid2[:8]}@t.com",
            password_hash="h",
            credits=10.0,
            subscription_tier="payg",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([u1, u2])
        db.commit()
        svc = CreditService(db)
        with pytest.raises(InsufficientCreditsError):
            svc.transfer_credits(uid1, uid2, 100.0)

    def test_transfer_zero_raises(self, db, test_user, regular_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.transfer_credits(test_user.id, regular_user.id, 0)

    def test_transfer_missing_source_raises(self, db, regular_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.transfer_credits("nope", regular_user.id, 5)

    def test_transfer_missing_dest_raises(self, db, test_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.transfer_credits(test_user.id, "nope", 5)


class TestResetCredits:
    def test_reset_succeeds(self, db, test_user):
        svc = CreditService(db)
        result = svc.reset_credits(test_user.id, 0.0)
        assert result["new_balance"] == 0.0

    def test_reset_negative_raises(self, db, test_user):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.reset_credits(test_user.id, -10)

    def test_reset_missing_user_raises(self, db):
        svc = CreditService(db)
        with pytest.raises(ValueError):
            svc.reset_credits("nonexistent", 0)
