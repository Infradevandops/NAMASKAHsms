"""Integration tests for Phase C and Phase D implementations."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.transaction import Transaction
from app.services.revenue_recognition_service import RevenueRecognitionService
from app.services.tax_service import TaxService
from app.services.financial_statements_service import FinancialStatementsService
from app.services.provider_settlement_service import ProviderSettlementService
from app.services.monitoring_service import MonitoringService
from app.services.analytics_service import AnalyticsService


class TestPhaseC_IntegrationFlow:
    """Integration tests for Phase C financial operations."""

    @pytest.fixture
    def setup_financial_data(self, db: Session):
        """Setup test financial data."""
        # Create test user
        user = User(
            id="integration_test_user",
            email="integration@test.com",
            credits=1000.0,
            email_verified=True,
        )
        db.add(user)

        # Create test transactions
        for i in range(10):
            transaction = Transaction(
                id=f"txn_integration_{i}",
                user_id="integration_test_user",
                amount=50.0 + i * 10,
                type="credit",
                service="sms",
                status="completed",
                created_at=datetime.now(timezone.utc) - timedelta(days=10 - i),
            )
            db.add(transaction)

        db.commit()
        return user

    @pytest.mark.asyncio
    async def test_complete_revenue_flow(self, db: Session, setup_financial_data):
        """Test complete revenue recognition and reporting flow."""
        # Initialize services
        revenue_service = RevenueRecognitionService(db)
        financial_service = FinancialStatementsService(db)

        # Step 1: Recognize revenue
        result = await revenue_service.recognize_revenue(
            transaction_id="txn_integration_0",
            gross_amount=50.0,
            provider_cost=15.0,
            tax_jurisdiction="US",
        )
        assert result["status"] == "success"
        assert result["net_amount"] == 35.0

        # Step 2: Get revenue summary
        summary = await revenue_service.get_revenue_by_period(
            period="2026-04", user_id="integration_test_user"
        )
        assert summary["gross_revenue"] >= 50.0

        # Step 3: Generate financial statements
        income_stmt = await financial_service.generate_income_statement(
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
        )
        assert income_stmt["status"] == "success"
        assert "revenue" in income_stmt

    @pytest.mark.asyncio
    async def test_complete_tax_flow(self, db: Session, setup_financial_data):
        """Test complete tax reporting flow."""
        from app.models.tax_report import TaxJurisdictionConfig

        tax_service = TaxService(db)

        # Setup jurisdiction config
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

        # Generate tax report
        report_result = await tax_service.generate_tax_report(
            period="2026-04",
            jurisdiction="US",
            report_type="VAT",
        )
        assert report_result["status"] == "success"

        # Record tax payment
        payment_result = await tax_service.record_tax_payment(
            report_id=report_result["report_id"],
            payment_amount=report_result["tax_amount_due"],
            payment_method="bank_transfer",
            payment_reference="PAY-2026-04-001",
        )
        assert payment_result["status"] == "success"

        # Get tax summary
        summary = await tax_service.get_tax_summary(year=2026)
        assert summary is not None
        assert "total_tax_due" in summary

    @pytest.mark.asyncio
    async def test_complete_provider_settlement_flow(self, db: Session):
        """Test complete provider settlement flow."""
        settlement_service = ProviderSettlementService(db)

        # Create settlement
        settlement_result = await settlement_service.create_settlement(
            provider_id="provider_integration_test",
            period="2026-04",
            total_messages=50000,
            successful_messages=49500,
            per_message_cost=0.01,
        )
        assert settlement_result["status"] == "success"

        # Track daily costs
        cost_result = await settlement_service.track_daily_costs(
            provider_id="provider_integration_test",
            messages_sent=5000,
            successful_sends=4950,
            per_message_rate=0.01,
        )
        assert cost_result["status"] == "success"

        # Record payment
        payment_result = await settlement_service.record_settlement_payment(
            settlement_id=settlement_result["settlement_id"],
            paid_amount=settlement_result["total_cost"] / 2,
            payment_method="bank_transfer",
            payment_reference="SETTLE-2026-04-001",
        )
        assert payment_result["status"] == "success"
        assert payment_result["remaining_balance"] > 0

        # Reconcile settlement
        reconciliation = await settlement_service.reconcile_settlement(
            settlement_id=settlement_result["settlement_id"],
            provider_invoice_count=50000,
            provider_invoice_cost=settlement_result["total_cost"],
        )
        assert reconciliation["status"] == "success"


class TestPhaseD_MonitoringFlow:
    """Integration tests for Phase D monitoring and analytics."""

    @pytest.mark.asyncio
    async def test_monitoring_service_flow(self, db: Session):
        """Test monitoring service."""
        monitoring_service = MonitoringService()

        # Collect system metrics
        metrics = await monitoring_service.collect_system_metrics()
        assert metrics is not None
        assert "requests" in metrics
        assert "performance" in metrics

        # Check alerts
        alerts = await monitoring_service.check_alerts()
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_analytics_service_flow(self, db: Session):
        """Test analytics service."""
        analytics_service = AnalyticsService(db)

        # Get overview
        overview = await analytics_service.get_overview()
        assert overview is not None
        assert "users" in overview
        assert "revenue" in overview

        # Get timeseries
        timeseries = await analytics_service.get_timeseries(days=30)
        assert timeseries is not None


class TestEndToEnd_FinancialFlow:
    """End-to-end financial flow tests."""

    @pytest.mark.asyncio
    async def test_complete_monthly_closing(self, db: Session):
        """Test complete monthly financial closing process."""
        # Setup
        user = User(
            id="monthly_test_user",
            email="monthly@test.com",
            credits=5000.0,
            email_verified=True,
        )
        db.add(user)

        # Create transactions for the month
        month_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
        month_end = datetime(2026, 4, 30, tzinfo=timezone.utc)

        for day in range(1, 31):
            txn_date = month_start + timedelta(days=day - 1)
            transaction = Transaction(
                id=f"txn_monthly_{day}",
                user_id="monthly_test_user",
                amount=100.0 + day * 5,
                type="credit",
                service="sms",
                status="completed",
                created_at=txn_date,
            )
            db.add(transaction)

        db.commit()

        # Initialize services
        revenue_service = RevenueRecognitionService(db)
        tax_service = TaxService(db)
        financial_service = FinancialStatementsService(db)
        settlement_service = ProviderSettlementService(db)

        # 1. Recognize all revenues
        for day in range(1, 31):
            txn_id = f"txn_monthly_{day}"
            await revenue_service.recognize_revenue(
                transaction_id=txn_id,
                gross_amount=100.0 + day * 5,
                provider_cost=(100.0 + day * 5) * 0.3,
                tax_jurisdiction="US",
            )

        # 2. Generate income statement
        income_stmt = await financial_service.generate_income_statement(
            period_start=month_start,
            period_end=month_end,
        )
        assert income_stmt["status"] == "success"

        # 3. Calculate ratios
        ratios = await financial_service.calculate_financial_ratios(
            period_start=month_start,
            period_end=month_end,
        )
        assert ratios is not None

        # 4. Record operating metrics
        metrics = await financial_service.record_operating_metrics(
            period="2026-04"
        )
        assert metrics is not None

        # 5. Create provider settlement
        settlement = await settlement_service.create_settlement(
            provider_id="provider_monthly_test",
            period="2026-04",
            total_messages=100000,
            successful_messages=98000,
            per_message_cost=0.005,
        )
        assert settlement["status"] == "success"

        print("\n✅ Monthly closing completed successfully!")
        print(f"   Revenue: ${income_stmt['revenue']:.2f}")
        print(f"   Net Income: ${income_stmt['net_income']:.2f}")
        print(f"   Settlement: ${settlement['total_cost']:.2f}")
