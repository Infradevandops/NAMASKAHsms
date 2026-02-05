"""Database models package."""

from .affiliate import AffiliateApplication, AffiliateCommission, AffiliateProgram
from .api_key import APIKey  # Import from separate api_key module
from .balance_transaction import BalanceTransaction
from .base import Base, BaseModel
from .commission import CommissionTier, PayoutRequest, RevenueShare
from .device_token import DeviceToken
from .enterprise import EnterpriseAccount, EnterpriseTier
from .notification import Notification
from .notification_preference import NotificationPreference, NotificationPreferenceDefaults
from .reseller import (
    BulkOperation,
    CreditAllocation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)
from .subscription_tier import SubscriptionTier
from .system import (
    ActivityLog,
    BannedNumber,
    InAppNotification,
    ServiceStatus,
    SupportTicket,
)
from .transaction import PaymentLog, Transaction
from .user import (
    NotificationSettings,
    Referral,
    Subscription,
    User,
    Webhook,
)
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
    # Transaction models
    "Transaction",
    "PaymentLog",
    # System models
    "ServiceStatus",
    "SupportTicket",
    "ActivityLog",
    "BannedNumber",
    "InAppNotification",
    # White - label models
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
    # Reseller models
    "BulkOperation",
    "CreditAllocation",
    "ResellerAccount",
    "SubAccount",
    "SubAccountTransaction",
]