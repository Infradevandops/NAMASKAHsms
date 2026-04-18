"""Financial statement and reporting models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String

from app.models.base import BaseModel


class FinancialStatement(BaseModel):
    """Generated financial statements."""

    __tablename__ = "financial_statements"

    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    period_type = Column(String, nullable=False)  # monthly, quarterly, annual
    reporting_entity = Column(String, nullable=False)  # Company name or entity ID

    # Statement type
    statement_type = Column(
        String, nullable=False, index=True
    )  # income, balance_sheet, cash_flow, equity

    # Income Statement
    revenue = Column(Float, default=0.0)
    cost_of_revenue = Column(Float, default=0.0)
    gross_profit = Column(Float, default=0.0)
    operating_expenses = Column(Float, default=0.0)
    operating_income = Column(Float, default=0.0)
    interest_expense = Column(Float, default=0.0)
    tax_expense = Column(Float, default=0.0)
    net_income = Column(Float, default=0.0)

    # Balance Sheet
    current_assets = Column(Float, default=0.0)
    fixed_assets = Column(Float, default=0.0)
    total_assets = Column(Float, default=0.0)
    current_liabilities = Column(Float, default=0.0)
    long_term_liabilities = Column(Float, default=0.0)
    total_liabilities = Column(Float, default=0.0)
    stockholders_equity = Column(Float, default=0.0)

    # Cash Flow
    operating_cash_flow = Column(Float, default=0.0)
    investing_cash_flow = Column(Float, default=0.0)
    financing_cash_flow = Column(Float, default=0.0)
    net_cash_flow = Column(Float, default=0.0)
    beginning_cash_balance = Column(Float, default=0.0)
    ending_cash_balance = Column(Float, default=0.0)

    # Key ratios
    gross_margin = Column(Float, default=0.0)
    operating_margin = Column(Float, default=0.0)
    net_margin = Column(Float, default=0.0)
    current_ratio = Column(Float, default=0.0)
    debt_to_equity = Column(Float, default=0.0)
    roe = Column(Float, default=0.0)  # Return on equity
    roa = Column(Float, default=0.0)  # Return on assets

    # Detailed breakdown
    line_items = Column(JSON)  # Detailed line items for each section
    notes = Column(JSON)  # Footnotes and explanations
    accounting_policies = Column(JSON)  # Methods used

    # Audit & Review
    status = Column(String, default="draft", nullable=False)  # draft, reviewed, final
    reviewed_by = Column(String)  # Accountant or auditor
    reviewed_at = Column(DateTime)
    approval_status = Column(String, default="pending")  # pending, approved, rejected
    approved_by = Column(String)
    approved_at = Column(DateTime)

    # Generated info
    generated_by = Column(String)  # System or user
    generated_at = Column(DateTime, nullable=False)
    generated_from_data_until = Column(DateTime)
    is_provisional = Column(Boolean, default=True)
    notes_field = Column(String)


class FinancialRatio(BaseModel):
    """Pre-calculated financial ratios for analysis."""

    __tablename__ = "financial_ratios"

    period = Column(String, nullable=False, index=True)  # YYYY-MM
    reporting_entity = Column(String, nullable=False, index=True)

    # Profitability Ratios
    gross_profit_margin = Column(Float)  # (Gross Profit / Revenue) * 100
    operating_profit_margin = Column(Float)  # (Operating Income / Revenue) * 100
    net_profit_margin = Column(Float)  # (Net Income / Revenue) * 100
    return_on_assets = Column(Float)  # (Net Income / Total Assets) * 100
    return_on_equity = Column(Float)  # (Net Income / Equity) * 100

    # Liquidity Ratios
    current_ratio = Column(Float)  # Current Assets / Current Liabilities
    quick_ratio = Column(Float)  # (Current Assets - Inventory) / Current Liabilities
    cash_ratio = Column(Float)  # Cash / Current Liabilities

    # Efficiency Ratios
    asset_turnover = Column(Float)  # Revenue / Average Total Assets
    inventory_turnover = Column(Float)  # COGS / Average Inventory
    receivables_turnover = Column(Float)  # Revenue / Average Receivables

    # Leverage Ratios
    debt_to_equity = Column(Float)  # Total Debt / Total Equity
    debt_to_assets = Column(Float)  # Total Debt / Total Assets
    equity_ratio = Column(Float)  # Total Equity / Total Assets
    interest_coverage = Column(Float)  # EBIT / Interest Expense

    # Growth Ratios
    revenue_growth_yoy = Column(Float)  # Year-over-year %
    income_growth_yoy = Column(Float)  # Year-over-year %
    asset_growth_yoy = Column(Float)  # Year-over-year %

    # Cash Flow Ratios
    operating_cash_flow_ratio = Column(Float)  # Operating CF / Current Liabilities
    free_cash_flow = Column(Float)  # Operating CF - Capital Expenditures
    cash_flow_to_net_income = Column(Float)  # Operating CF / Net Income

    # Calculated at
    calculated_at = Column(DateTime, nullable=False)
    calculated_by = Column(String)


class BudgetVsActual(BaseModel):
    """Budget vs actual analysis."""

    __tablename__ = "budget_vs_actual"

    period = Column(String, nullable=False, index=True)  # YYYY-MM
    category = Column(
        String, nullable=False, index=True
    )  # revenue, cogs, operating_exp, etc.

    # Budget
    budgeted_amount = Column(Float, nullable=False)
    budget_basis = Column(String)  # historical, forecast, zero_based

    # Actual
    actual_amount = Column(Float, nullable=False)
    actual_sources = Column(JSON)  # Where this came from

    # Variance
    variance_amount = Column(Float, nullable=False)  # Actual - Budgeted
    variance_percentage = Column(Float, nullable=False)  # (Variance / Budget) * 100
    variance_reason = Column(String)  # Explanation of variance
    is_favorable = Column(Boolean)  # True if variance is good

    # Trend
    trend = Column(String)  # improving, declining, stable
    prior_period_variance = Column(Float)  # Last period's variance for comparison

    # Investigation
    investigated = Column(Boolean, default=False)
    investigation_notes = Column(String)
    investigated_by = Column(String)
    investigated_at = Column(DateTime)

    # Action items
    action_required = Column(Boolean, default=False)
    action_description = Column(String)
    action_owner = Column(String)
    action_due_date = Column(DateTime)


class OperatingMetrics(BaseModel):
    """Key operating metrics for business health."""

    __tablename__ = "operating_metrics"

    period = Column(String, nullable=False, index=True)  # YYYY-MM
    metric_date = Column(DateTime, nullable=False, index=True)

    # User metrics
    total_active_users = Column(Float)
    new_users_acquired = Column(Float)
    churned_users = Column(Float)
    paying_users = Column(Float)

    # Usage metrics
    total_transactions = Column(Float)
    successful_transactions = Column(Float)
    failed_transactions = Column(Float)
    transaction_success_rate = Column(Float)

    # Financial metrics
    average_revenue_per_user = Column(Float)  # ARPU
    average_transaction_value = Column(Float)  # ATV
    lifetime_value = Column(Float)  # LTV (estimated)
    customer_acquisition_cost = Column(Float)  # CAC
    payback_period = Column(Float)  # Months to recover CAC

    # Refund metrics
    refund_rate = Column(Float)  # Refunds / Total Revenue %
    chargeback_rate = Column(Float)  # Chargebacks / Transactions %
    dispute_rate = Column(Float)  # Disputes / Transactions %

    # Operational metrics
    average_response_time = Column(Float)  # In seconds
    error_rate = Column(Float)  # Errors / Requests %
    availability = Column(Float)  # Uptime %

    # Service metrics
    services_used = Column(JSON)  # {service: count}
    top_service = Column(String)
    geographic_breakdown = Column(JSON)  # {country: count}

    # Trends
    mom_growth = Column(Float)  # Month-over-month %
    qoq_growth = Column(Float)  # Quarter-over-quarter %
    yoy_growth = Column(Float)  # Year-over-year %

    # Notes
    notes = Column(String)
