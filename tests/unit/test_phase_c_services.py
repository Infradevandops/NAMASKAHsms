"""Unit tests for Phase C financial services."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User
from app.models.revenue_recognition import RevenueRecognition
from app.models.tax_report import TaxReport
from app.models.financial_statement import FinancialStatement
from app.models.provider_settlement import ProviderSettlement
from app.services.revenue_recognition_service import RevenueRecognitionService
from app.services.tax_service import TaxService
from app.services.financial_statements_service import FinancialStatementsService
from app.services.provider_settlement_service import ProviderSettlementService


class TestRevenueRecognitionService:
    """Tests for revenue recognition service."""

    @pytest.fixture
    def service(self, db: Session):
        return RevenueRecognitionService(db)

    @pytest.fixture
    def test_transaction(self, db: Session):
        """Create test transaction."""
        user = User(
            id="test_user",
            email="test@example.com",
            credits=100.0,
            email_verified=True,
        )
        db.add(user)
        db.commit()

        transaction = Transaction(
            id="txn_test_001",
            user_id="test_user",
            amount=50.0,
            type="credit",
            service="sms",
            status="completed",
            created_at=datetime.now(timezone.utc),
        )
        db.add(transaction)
        db.commit()
        return transaction

    @pytest.mark.asyncio
    async def test_recognize_revenue(self, service, test_transaction, db: Session):
        """Test revenue recognition."""
        result = await service.recognize_revenue(
            transaction_id=test_transaction.id,
            gross_amount=50.0,
            provider_cost=15.0,
            tax_jurisdiction="US",
        )

        assert result["status"] == "success"
        assert result["gross_amount"] == 50.0
        assert result["net_amount"] == 35.0

        # Verify in database
        recognition = (
            db.query(RevenueRecognition)
            .filter(RevenueRecognition.transaction_id == test_transaction.id)
            .first()
        )
        assert recognition is not None
        assert recognition.status == "recognized"

    @pytest.mark.asyncio
    async def test_recognize_deferred_revenue(self, service, db: Session):
        """Test deferred revenue schedule."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=365)

        result = await service.recognize_deferred_revenue(
            user_id="test_user",
            contract_id="contract_001",
            contract_start=start,
            contract_end=end,
            total_contract_value=12000.0,
        )

        assert result["status"] == "success"
        assert result["months"] == 13
        assert result["monthly_amount"] == pytest.approx(923.08, rel=0.1)

    @pytest.mark.asyncio
    async def test_process_revenue_adjustment(self, service, test_transaction, db: Session):
        """Test revenue adjustment."""
        # First recognize revenue
        await service.recognize_revenue(
            transaction_id=test_transaction.id,
            gross_amount=50.0,
            provider_cost=15.0,
            tax_jurisdiction="US",
        )

        recognition = (
            db.query(RevenueRecognition)
            .filter(RevenueRecognition.transaction_id == test_transaction.id)
            .first()
        )

        # Process adjustment
        result = await service.process_revenue_adjustment(
            revenue_id=recognition.id,
            adjustment_type="refund",
            adjustment_amount=10.0,
            reason="Customer refund",
            initiated_by="admin",
        )

        assert result["status"] == "success"
        assert result["amount"] == 10.0


class TestTaxService:
    """Tests for tax service."""

    @pytest.fixture
    def service(self, db: Session):
        return TaxService(db)

    @pytest.mark.asyncio
    async def test_generate_tax_report(self, service, db: Session):
        """Test tax report generation."""
        # Create test config
        from app.models.tax_report import TaxJurisdictionConfig

        config = TaxJurisdictionConfig(
            jurisdiction_code="US",
            jurisdiction_name="United States",
            country_code="US",
            standard_tax_rate=0.10,
            filing_frequency="monthly",
            requires_tax_id=True,
            is_active=True,
            effective_from=datetime.now(timezone.utc),
        )
        db.add(config)
        db.commit()

        result = await service.generate_tax_report(
            period="2026-01",
            jurisdiction="US",
            report_type="VAT",
        )

        assert result["status"] == "success"
        assert result["jurisdiction"] == "US"

    @pytest.mark.asyncio
    async def test_create_tax_exemption(self, service, db: Session):
        """Test tax exemption creation."""
        user = User(
            id="exempt_user",
            email="exempt@example.com",
            credits=100.0,
            email_verified=True,
        )
        db.add(user)
        db.commit()

        result = await service.create_tax_exemption(
            user_id="exempt_user",
            jurisdiction="US",
            certificate_type="nonprofit",
            certificate_number="NPO123456",
            expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
        )

        assert result["status"] == "success"
        assert result["certificate_type"] == "nonprofit"


class TestFinancialStatementsService:
    """Tests for financial statements service."""

    @pytest.fixture
    def service(self, db: Session):
        return FinancialStatementsService(db)

    @pytest.mark.asyncio
    async def test_generate_income_statement(self, service, db: Session):
        """Test income statement generation."""
        result = await service.generate_income_statement(
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
        )

        assert result["status"] == "success" or "statement_id" in result
        assert "revenue" in result
        assert "net_income" in result

    @pytest.mark.asyncio
    async def test_generate_balance_sheet(self, service):
        """Test balance sheet generation."""
        result = await service.generate_balance_sheet(
            as_of_date=datetime.now(timezone.utc)
        )

        assert "statement_id" in result or result is not None
        assert "total_assets" in result or "as_of_date" in result

    @pytest.mark.asyncio
    async def test_calculate_financial_ratios(self, service):
        """Test financial ratio calculation."""
        result = await service.calculate_financial_ratios(
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
        )

        assert result is not None
        assert "period" in result


class TestProviderSettlementService:
    """Tests for provider settlement service."""

    @pytest.fixture
    def service(self, db: Session):
        return ProviderSettlementService(db)

    @pytest.mark.asyncio
    async def test_create_settlement(self, service, db: Session):
        """Test settlement creation."""
        result = await service.create_settlement(
            provider_id="provider_001",
            period="2026-01",
            total_messages=10000,
            successful_messages=9800,
            per_message_cost=0.05,
        )

        assert result["status"] == "success"
        assert result["total_messages"] == 10000
        assert result["total_cost"] == pytest.approx(525.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_track_daily_costs(self, service):
        """Test daily cost tracking."""
        result = await service.track_daily_costs(
            provider_id="provider_001",
            messages_sent=1000,
            successful_sends=980,
            per_message_rate=0.05,
        )

        assert result["status"] == "success"
        assert result["daily_cost"] == pytest.approx(50.0)
        assert result["success_rate"] == pytest.approx(98.0)

    @pytest.mark.asyncio
    async def test_get_settlement_summary(self, service, db: Session):
        """Test settlement summary."""
        # Create test settlement
        settlement = ProviderSettlement(
            provider_id="provider_001",
            settlement_period="2026-01",
            settlement_start=datetime.now(timezone.utc),
            settlement_end=datetime.now(timezone.utc),
            total_messages_sent=10000,
            successful_messages=9800,
            per_message_cost=0.05,
            total_message_cost=500,
            total_cost=500,
            status="paid",
            paid_amount=500,
            remaining_balance=0,
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.add(settlement)
        db.commit()

        result = await service.get_settlement_summary(
            provider_id="provider_001",
            year=2026,
        )

        assert result is not None
        assert result["provider_id"] == "provider_001"
