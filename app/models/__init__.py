"""Database models package."""

from .activity import Activity
from .affiliate import AffiliateApplication, AffiliateCommission, AffiliateProgram
from .analytics import (
    AnalyticsCache,
    CustomReport,
    ScheduledReport,
    UserAnalyticsSnapshot,
    VerificationEvent,
    VerificationStatistics,
)
from .admin_notification import AdminNotification
from .monthly_target import MonthlyTarget
from .daily_user_snapshot import DailyUserSnapshot
from .api_key import APIKey  # Import from separate api_key module
from .balance_transaction import BalanceTransaction
from .base import Base, BaseModel
from .carrier_analytics import CarrierAnalytics
from .commission import CommissionTier, PayoutRequest, RevenueShare
from .device_token import DeviceToken
from .dispute import Dispute
from .enterprise import EnterpriseAccount, EnterpriseTier
from .financial_statement import (
    BudgetVsActual,
    FinancialRatio,
    FinancialStatement,
    OperatingMetrics,
)
from .notification import Notification
from .notification_preference import (
    NotificationPreference,
    NotificationPreferenceDefaults,
)
from .price_snapshot import PriceSnapshot
from .pricing_template import (
    PricingHistory,
    PricingTemplate,
    TierPricing,
    UserPricingAssignment,
)
from .provider_settlement import (
    PayoutSchedule,
    ProviderAgreement,
    ProviderCostTracking,
    ProviderReconciliation,
    ProviderSettlement,
)
from .reconciliation_log import BalanceMismatchAlert, ReconciliationLog
from .reseller import (
    BulkOperation,
    CreditAllocation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)
from .revenue_recognition import (
    AccrualTrackingLog,
    DeferredRevenueSchedule,
    RevenueAdjustment,
    RevenueRecognition,
)
from .subscription_tier import SubscriptionTier
from .system import (
    ActivityLog,
    BannedNumber,
    InAppNotification,
    ServiceStatus,
    SupportTicket,
)
from .tax_report import (
    TaxExemptionCertificate,
    TaxJurisdictionConfig,
    TaxReport,
    WithholdingTaxRecord,
)
from .transaction import PaymentLog, Transaction
from .user import NotificationSettings, Referral, Subscription, User, Webhook
from .user_preference import UserPreference
from .user_quota import MonthlyQuotaUsage
from .verification import NumberRental, Verification, VerificationReceipt
from .whitelabel import WhiteLabelConfig
from .whitelabel_enhanced import (
    PartnerFeature,
    WhiteLabelAsset,
    WhiteLabelDomain,
    WhiteLabelTheme,
)

__all__ = [
    # Base
    "BaseModel",
    "Base",
    # Analytics models
    "AnalyticsCache",
    "VerificationEvent",
    "CustomReport",
    "ScheduledReport",
    "UserAnalyticsSnapshot",
    "VerificationStatistics",
    # User models
    "User",
    "APIKey",
    "Webhook",
    "NotificationSettings",
    "Referral",
    "Subscription",
    "SubscriptionTier",
    "UserPreference",
    "MonthlyQuotaUsage",
    "DeviceToken",
    "Notification",
    "NotificationPreference",
    "NotificationPreferenceDefaults",
    "BalanceTransaction",
    # Verification models
    "Verification",
    "NumberRental",
    "VerificationReceipt",
    "CarrierAnalytics",
    # Transaction models
    "Transaction",
    "PaymentLog",
    # System models
    "ServiceStatus",
    "SupportTicket",
    "ActivityLog",
    "BannedNumber",
    "InAppNotification",
    # White-label models
    "WhiteLabelConfig",
    "PartnerFeature",
    "WhiteLabelAsset",
    "WhiteLabelDomain",
    "WhiteLabelTheme",
    # Enterprise models
    "EnterpriseAccount",
    "EnterpriseTier",
    # Affiliate models
    "AffiliateApplication",
    "AffiliateCommission",
    "AffiliateProgram",
    # Commission models
    "CommissionTier",
    "PayoutRequest",
    "RevenueShare",
    # Financial models - Phase C
    "RevenueRecognition",
    "DeferredRevenueSchedule",
    "RevenueAdjustment",
    "AccrualTrackingLog",
    "TaxReport",
    "TaxJurisdictionConfig",
    "TaxExemptionCertificate",
    "WithholdingTaxRecord",
    "FinancialStatement",
    "FinancialRatio",
    "BudgetVsActual",
    "OperatingMetrics",
    # Provider settlement models - Phase C
    "ProviderSettlement",
    "ProviderCostTracking",
    "PayoutSchedule",
    "ProviderReconciliation",
    "ProviderAgreement",
    # Reseller models
    "BulkOperation",
    "CreditAllocation",
    "ResellerAccount",
    "SubAccount",
    "SubAccountTransaction",
    "Activity",
    # Admin Pricing & Notifications
    "PriceSnapshot",
    "AdminNotification",
    "PricingTemplate",
    "TierPricing",
    "PricingHistory",
    "UserPricingAssignment",
    "MonthlyTarget",
    "DailyUserSnapshot",
]
