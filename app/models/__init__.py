"""Database models package."""
from .base import Base, BaseModel
from .system import (
    ActivityLog,
    BannedNumber,
    InAppNotification,
    ServiceStatus,
    SupportTicket,
)
from .transaction import PaymentLog, Transaction
from .user import (
    NotificationPreferences,
    NotificationSettings,
    Referral,
    Subscription,
    User,
    Webhook,
)
from .api_key import APIKey  # Import from separate api_key module
from .verification import NumberRental, Verification, VerificationReceipt
from .whitelabel import WhiteLabelConfig
from .whitelabel_enhanced import (
    PartnerFeature,
    WhiteLabelAsset,
    WhiteLabelDomain,
    WhiteLabelTheme,
)
from .enterprise import EnterpriseAccount, EnterpriseTier
from .affiliate import AffiliateApplication, AffiliateCommission, AffiliateProgram
from .commission import CommissionTier, PayoutRequest, RevenueShare
from .reseller import (
    BulkOperation,
    CreditAllocation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)
from .personal_number import PersonalNumber

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
    "NotificationPreferences",
    "UserPreference",
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
    # Personal number model
    "PersonalNumber",
]
