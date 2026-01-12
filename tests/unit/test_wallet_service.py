"""Unit tests for wallet service business logic."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.payment_service import PaymentService
from app.models.user import User
from app.models.transaction import Transaction


class TestWalletCreditCalculations:
    """Test credit calculation logic."""
    
    def test_calculate_bonus_credits_tier_freemium(self, db_session):
        """Freemium: 11% bonus (9 SMS per $20 = $2.22/SMS)."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=0
        )
        db_session.add(user)
        db_session.commit()
        
        payment_service = PaymentService(db_session)
        bonus = payment_service.calculate_bonus(20.0, 'freemium')
        
        # 11% bonus on $20 = $2.20 (approximately)
        assert bonus >= 2.0
        assert bonus <= 2.5
    
    def test_calculate_bonus_credits_tier_payg(self, db_session):
        """PAYG: No bonus."""
        payment_service = PaymentService(db_session)
        bonus = payment_service.calculate_bonus(20.0, 'payg')
        assert bonus == 0
    
    def test_calculate_bonus_credits_tier_pro(self, db_session):
        """Pro: 5% bonus."""
        payment_service = PaymentService(db_session)
        bonus = payment_service.calculate_bonus(100.0, 'pro')
        assert bonus == 5.0
    
    def test_calculate_bonus_credits_tier_custom(self, db_session):
        """Custom: 10% bonus."""
        payment_service = PaymentService(db_session)
        bonus = payment_service.calculate_bonus(100.0, 'custom')
        assert bonus == 10.0
    
    def test_calculate_sms_cost_base(self):
        """Base SMS cost: $2.50."""
        from app.helpers.tier_helpers import calculate_sms_cost
        cost = calculate_sms_cost('payg', {})
        assert cost == 2.50
    
    def test_calculate_sms_cost_with_location_filter(self):
        """Location filter: +$0.25."""
        from app.helpers.tier_helpers import calculate_sms_cost
        cost = calculate_sms_cost('payg', {'location': 'CA'})
        assert cost == 2.75
    
    def test_calculate_sms_cost_with_isp_filter(self):
        """ISP filter: +$0.50."""
        from app.helpers.tier_helpers import calculate_sms_cost
        cost = calculate_sms_cost('payg', {'isp': 'T-Mobile'})
        assert cost == 3.00
    
    def test_calculate_sms_cost_with_all_filters(self):
        """All filters: +$0.75."""
        from app.helpers.tier_helpers import calculate_sms_cost
        cost = calculate_sms_cost('payg', {'location': 'CA', 'isp': 'T-Mobile'})
        assert cost == 3.25
    
    def test_calculate_sms_cost_pro_tier_no_extra(self):
        """Pro tier: Filters included."""
        from app.helpers.tier_helpers import calculate_sms_cost
        cost = calculate_sms_cost('pro', {'location': 'CA', 'isp': 'T-Mobile'})
        # Pro tier overage rate
        assert cost == 0.30


class TestWalletTransactions:
    """Test transaction recording."""
    
    def test_record_deposit_transaction(self, db_session):
        """Test recording a deposit transaction."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=0
        )
        db_session.add(user)
        db_session.commit()
        
        tx = Transaction(
            user_id=user.id,
            type='deposit',
            amount=20.0,
            description='Paystack deposit',
            metadata={'bonus': 2.22}
        )
        db_session.add(tx)
        db_session.commit()
        
        assert tx.type == 'deposit'
        assert tx.amount == 20.0
        assert tx.metadata['bonus'] == 2.22
    
    def test_record_deduction_transaction(self, db_session):
        """Test recording a deduction transaction."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()
        
        tx = Transaction(
            user_id=user.id,
            type='deduction',
            amount=-2.50,
            description='SMS verification',
            metadata={'sms_id': '123'}
        )
        db_session.add(tx)
        db_session.commit()
        
        assert tx.type == 'deduction'
        assert tx.amount == -2.50
    
    def test_transaction_history_pagination(self, db_session):
        """Test transaction history pagination."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=100.0
        )
        db_session.add(user)
        db_session.commit()
        
        # Create 100 transactions
        for i in range(100):
            tx = Transaction(
                user_id=user.id,
                type='deposit',
                amount=10.0,
                description=f'Deposit {i}'
            )
            db_session.add(tx)
        db_session.commit()
        
        # Get first page
        page1 = db_session.query(Transaction).filter(
            Transaction.user_id == user.id
        ).limit(50).all()
        assert len(page1) == 50
        
        # Get second page
        page2 = db_session.query(Transaction).filter(
            Transaction.user_id == user.id
        ).offset(50).limit(50).all()
        assert len(page2) == 50


class TestWalletBalanceOperations:
    """Test wallet balance operations."""
    
    def test_deduct_credits_sufficient_balance(self, db_session):
        """User has $10, deduct $5."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()
        
        # Deduct credits
        user.credits -= 5.0
        db_session.commit()
        
        assert user.credits == 5.0
    
    def test_deduct_credits_insufficient_balance(self, db_session):
        """User has $3, try to deduct $5."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=3.0
        )
        db_session.add(user)
        db_session.commit()
        
        # Check if sufficient
        has_sufficient = user.credits >= 5.0
        assert has_sufficient == False
    
    def test_deduct_credits_with_free_verifications(self, db_session):
        """User has 2 free verifications."""
        user = User(
            email="test@example.com",
            tier_id="freemium",
            credits=0,
            free_verifications=2.0
        )
        db_session.add(user)
        db_session.commit()
        
        # Use free verification
        if user.free_verifications > 0:
            user.free_verifications -= 1
            db_session.commit()
        
        assert user.free_verifications == 1.0
        assert user.credits == 0


@pytest.fixture
def db_session(db_session):
    """Provide database session for tests."""
    return db_session
