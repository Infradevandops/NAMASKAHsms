

import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.api_key_service import APIKeyService
from app.services.transaction_service import TransactionService
from app.services.verification_pricing_service import VerificationPricingService

@pytest.fixture
def pro_user(db: Session):

    """Create pro tier user."""
    user = User(
        id=f"pro_{uuid.uuid4()}",
        email=f"pro_{uuid.uuid4()}@test.com",
        password_hash="hash",
        subscription_tier="pro",
        credits=100.0,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def freemium_user_with_bonus(db: Session):

    """Create freemium user with bonus."""
    user = User(
        id=f"freemium_{uuid.uuid4()}",
        email=f"freemium_{uuid.uuid4()}@test.com",
        password_hash="hash",
        subscription_tier="freemium",
        bonus_sms_balance=9.0,
        credits=0.0,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


class TestVerificationPricingService:

    """Test verification pricing service."""

    def test_validate_and_calculate_cost(self, db: Session, pro_user: User):

        """Test cost calculation."""
        cost_info = VerificationPricingService.validate_and_calculate_cost(db, pro_user.id)
        assert cost_info["total_cost"] > 0
        assert cost_info["tier"] == "pro"

    def test_validate_insufficient_balance(self, db: Session, pro_user: User):

        """Test insufficient balance check."""
        pro_user.credits = 0.0
        db.commit()

        with pytest.raises(ValueError, match="Insufficient balance"):
            VerificationPricingService.validate_and_calculate_cost(db, pro_user.id)

    def test_deduct_cost_pro(self, db: Session, pro_user: User):

        """Test cost deduction for pro user."""
        initial_balance = pro_user.credits
        VerificationPricingService.deduct_cost(db, pro_user.id, 2.50)

        pro_user = db.query(User).filter(User.id == pro_user.id).first()
        assert pro_user.credits == initial_balance - 2.50

    def test_deduct_cost_freemium(self, db: Session, freemium_user_with_bonus: User):

        """Test cost deduction for freemium user."""
        initial_bonus = freemium_user_with_bonus.bonus_sms_balance
        VerificationPricingService.deduct_cost(db, freemium_user_with_bonus.id, 2.50)

        freemium_user = db.query(User).filter(User.id == freemium_user_with_bonus.id).first()
        assert freemium_user.bonus_sms_balance == initial_bonus - 1

    def test_get_pricing_breakdown(self, db: Session, pro_user: User):

        """Test pricing breakdown."""
        breakdown = VerificationPricingService.get_pricing_breakdown(db, pro_user.id)
        assert breakdown["tier"] == "pro"
        assert breakdown["quota_limit"] == 15.0
        assert breakdown["user_balance"] == 100.0


class TestAPIKeyService:

        """Test API key service."""

    def test_can_create_key_freemium(self, db: Session, freemium_user_with_bonus: User):

        """Test freemium cannot create keys."""
        service = APIKeyService(db)
        assert service.can_create_key(freemium_user_with_bonus.id) is False

    def test_can_create_key_pro(self, db: Session, pro_user: User):

        """Test pro can create keys."""
        service = APIKeyService(db)
        assert service.can_create_key(pro_user.id) is True

    def test_get_remaining_keys_pro(self, db: Session, pro_user: User):

        """Test remaining keys for pro."""
        service = APIKeyService(db)
        remaining = service.get_remaining_keys(pro_user.id)
        assert remaining == 10

    def test_get_remaining_keys_freemium(self, db: Session, freemium_user_with_bonus: User):

        """Test remaining keys for freemium."""
        service = APIKeyService(db)
        remaining = service.get_remaining_keys(freemium_user_with_bonus.id)
        assert remaining == 0

    def test_create_key_pro(self, db: Session, pro_user: User):

        """Test creating key for pro user."""
        service = APIKeyService(db)
        raw_key, api_key = service.generate_api_key(pro_user.id, name="Test Key")
        assert api_key.name == "Test Key"
        assert raw_key is not None

    def test_create_key_freemium_fails(self, db: Session, freemium_user_with_bonus: User):

        """Test creating key for freemium fails."""
        service = APIKeyService(db)
        with pytest.raises(ValueError, match="API key limit reached"):
            service.generate_api_key(freemium_user_with_bonus.id)

    def test_create_key_limit_reached(self, db: Session, pro_user: User):

        """Test key limit enforcement."""
        service = APIKeyService(db)
        for i in range(10):
            service.generate_api_key(pro_user.id, name=f"Key {i}")

        with pytest.raises(ValueError, match="API key limit reached"):
            service.generate_api_key(pro_user.id)


class TestTransactionService:

        """Test transaction logging."""

    def test_log_sms_purchase(self, db: Session, pro_user: User):

        """Test logging SMS purchase."""
        tx_id = TransactionService.log_sms_purchase(db, pro_user.id, 2.50, "pro", "telegram")
        assert tx_id is not None

    def test_log_api_key_creation(self, db: Session, pro_user: User):

        """Test logging API key creation."""
        tx_id = TransactionService.log_api_key_creation(db, pro_user.id, "key-123")
        assert tx_id is not None

    def test_log_filter_charge(self, db: Session, pro_user: User):

        """Test logging filter charge."""
        tx_id = TransactionService.log_filter_charge(db, pro_user.id, 0.25, "state", "payg")
        assert tx_id is not None

    def test_log_overage_charge(self, db: Session, pro_user: User):

        """Test logging overage charge."""
        tx_id = TransactionService.log_overage_charge(db, pro_user.id, 1.50, "pro")
        assert tx_id is not None
