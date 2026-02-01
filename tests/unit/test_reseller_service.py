"""Unit tests for Reseller Service."""


import pytest
from app.models.reseller import (
from app.models.user import User
from app.services.reseller_service import ResellerService
from app.services.reseller_service import ResellerService
from app.services.reseller_service import get_reseller_service

    BulkOperation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)


@pytest.fixture
def service(db_session):

    return ResellerService(db_session)


def test_get_reseller_service(db_session):

    svc = get_reseller_service(db_session)
    assert svc is not None


@pytest.mark.asyncio
async def test_create_sub_account_invalid_reseller(service):
    res = await service.create_sub_account(99999, "Name", "email@ex.com")
    assert res["error"] == "Reseller account not found"


@pytest.mark.asyncio
async def test_allocate_credits_invalid_ids(service):
    res = await service.allocate_credits(999, 888, 10.0)
    assert res["error"] == "Invalid reseller or sub - account"


@pytest.mark.asyncio
async def test_bulk_credit_topup_partial_failure(service, regular_user, db_session):
    # Setup reseller
    res_res = await service.create_reseller_account(regular_user.id)
    rid = res_res["reseller_id"]

    # Sub1 success
    s1 = await service.create_sub_account(rid, "S1", "s1@ex.com")
    # Sub2 fail (not exists, ID 9999)

    regular_user.credits = 100.0
    db_session.commit()

    res = await service.bulk_credit_topup(rid, [s1["sub_account_id"], 9999], 10.0)
    assert res["processed"] == 1
    assert res["failed"] == 1
    assert len(res["errors"]) == 1


class TestResellerService:

    """Test reseller service functionality."""

    @pytest.fixture
def reseller_user(self, db_session):

        """Create a parent user who will be the reseller."""
        user = User(
            email="reseller@example.com",
            subscription_tier="pro",
            credits=1000.0,
            password_hash="hashed_pw",
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
def reseller_service(self, db_session):

        return ResellerService(db_session)

    @pytest.mark.asyncio
    async def test_create_reseller_account_success(self, db_session, reseller_service, reseller_user):
        """Test creating a reseller account."""
        result = await reseller_service.create_reseller_account(reseller_user.id, tier="gold")

        assert result["success"] is True
        assert result["tier"] == "gold"
        assert result["discount"] == 0.20  # Gold discount

        account = db_session.query(ResellerAccount).filter(ResellerAccount.user_id == reseller_user.id).first()
        assert account is not None
        assert account.credit_limit == 25000.0

    @pytest.mark.asyncio
    async def test_create_reseller_account_duplicate(self, db_session, reseller_service, reseller_user):
        """Test ensuring 1:1 user-reseller relationship."""
        await reseller_service.create_reseller_account(reseller_user.id)

        # Try again
        result = await reseller_service.create_reseller_account(reseller_user.id)
        assert "error" in result
        assert result["error"] == "User already has reseller account"

    @pytest.mark.asyncio
    async def test_create_sub_account(self, db_session, reseller_service, reseller_user):
        """Test creating a sub-account."""
        # Setup reseller
        res = await reseller_service.create_reseller_account(reseller_user.id)
        reseller_id = res["reseller_id"]

        result = await reseller_service.create_sub_account(
            reseller_id,
            name="Sub Client A",
            email="client_a@example.com",
            initial_credits=50.0,
        )

        assert result["success"] is True
        sub_id = result["sub_account_id"]

        sub = db_session.query(SubAccount).filter(SubAccount.id == sub_id).first()
        assert sub.name == "Sub Client A"
        assert sub.credits == 50.0
        assert sub.reseller_id == reseller_id

    @pytest.mark.asyncio
    async def test_create_sub_account_email_exists(self, db_session, reseller_service, reseller_user):
        """Test sub-account unique email constraint."""
        res = await reseller_service.create_reseller_account(reseller_user.id)
        reseller_id = res["reseller_id"]

        await reseller_service.create_sub_account(reseller_id, "A", "dup@example.com")
        result = await reseller_service.create_sub_account(reseller_id, "B", "dup@example.com")

        assert "error" in result
        assert result["error"] == "Email already exists"

    @pytest.mark.asyncio
    async def test_allocate_credits_success(self, db_session, reseller_service, reseller_user):
        """Test transferring credits from reseller to sub-account."""
        # Reseller has 1000 credits
        res = await reseller_service.create_reseller_account(reseller_user.id)
        reseller_id = res["reseller_id"]

        sub_res = await reseller_service.create_sub_account(reseller_id, "Sub", "sub@example.com", initial_credits=0)
        sub_id = sub_res["sub_account_id"]

        # Allocate 100
        result = await reseller_service.allocate_credits(reseller_id, sub_id, 100.0)

        assert result["success"] is True
        assert result["allocated_amount"] == 100.0

        # Check balances
        db_session.refresh(reseller_user)
        sub = db_session.query(SubAccount).filter(SubAccount.id == sub_id).first()

        assert reseller_user.credits == 900.0  # 1000 - 100
        assert sub.credits == 100.0

        # Check transaction log
        tx = db_session.query(SubAccountTransaction).filter(SubAccountTransaction.sub_account_id == sub_id).first()
        assert tx.amount == 100.0
        assert tx.transaction_type == "credit"

    @pytest.mark.asyncio
    async def test_allocate_credits_insufficient_funds(self, db_session, reseller_service, reseller_user):
        """Test error when reseller has insufficient funds."""
        res = await reseller_service.create_reseller_account(reseller_user.id)
        reseller_id = res["reseller_id"]

        sub_res = await reseller_service.create_sub_account(reseller_id, "Sub", "sub@example.com")
        sub_id = sub_res["sub_account_id"]

        # Try to allocate 5000 (User has 1000)
        result = await reseller_service.allocate_credits(reseller_id, sub_id, 5000.0)

        assert "error" in result
        assert result["error"] == "Insufficient reseller credits"

    @pytest.mark.asyncio
    async def test_bulk_credit_topup(self, db_session, reseller_service, reseller_user):
        """Test bulk credit operations."""
        res = await reseller_service.create_reseller_account(reseller_user.id)
        reseller_id = res["reseller_id"]

        # Create 3 sub-accounts
        subs = []
for i in range(3):
            r = await reseller_service.create_sub_account(reseller_id, f"Sub {i}", f"sub{i}@example.com")
            subs.append(r["sub_account_id"])

        # Bulk topup 50 each (Total 150)
        result = await reseller_service.bulk_credit_topup(reseller_id, subs, 50.0)

        assert result["success"] is True
        assert result["processed"] == 3
        assert result["failed"] == 0

        # Check reseller balance (1000 - 150 = 850)
        db_session.refresh(reseller_user)
        assert reseller_user.credits == 850.0

        # Check bulk op record
        op = db_session.query(BulkOperation).first()
        assert op.status == "completed"
        assert op.total_accounts == 3

    @pytest.mark.asyncio
    async def test_get_usage_report(self, db_session, reseller_service, reseller_user):
        """Test analytics report generation."""
        res = await reseller_service.create_reseller_account(reseller_user.id)
        reseller_id = res["reseller_id"]

        sub_res = await reseller_service.create_sub_account(reseller_id, "Sub", "sub@example.com")
        sub_id = sub_res["sub_account_id"]

        # Create some transactions
        # 1. Allocation (Credit)
        await reseller_service.allocate_credits(reseller_id, sub_id, 100.0)

        # 2. Manual Debit (Usage simulation)
        # We need to manually add a debit transaction as we don't have a 'debit' method exposed in ResellerService yet
        # (It likely happens in the SMS sending logic which uses SubAccountTransaction model directly)
        tx = SubAccountTransaction(
            sub_account_id=sub_id,
            transaction_type="debit",
            amount=5.0,
            description="SMS sent",
            balance_after=95.0,
        )
        db_session.add(tx)
        db_session.commit()

        report = await reseller_service.get_usage_report(reseller_id, days=7)

        assert report["total_sub_accounts"] == 1
        assert report["total_credits_allocated"] == 100.0
        assert report["total_usage"] == 5.0
        assert len(report["transactions"]) >= 2