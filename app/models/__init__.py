"""Database models package."""

from .affiliate import AffiliateApplication, AffiliateCommission, AffiliateProgram
from .base import Base, BaseModel
from .commission import CommissionTier, PayoutRequest, RevenueShare
from .enterprise import EnterpriseAccount, EnterpriseTier
from .personal_number import PersonalNumber
from .reseller import (
    BulkOperation,
    CreditAllocation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)
from .system import (
    ActivityLog,
    BannedNumber,
    InAppNotification,
    ServiceStatus,
    SupportTicket,
)
from .transaction import PaymentLog, Transaction
from .user import (
    APIKey,
    NotificationPreferences,
    NotificationSettings,
    Referral,
    Subscription,
    User,
    Webhook,
)
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
    "NotificationPreferences",
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
    # Reseller models
    "BulkOperation",
    "CreditAllocation",
    "ResellerAccount",
    "SubAccount",
    "SubAccountTransaction",
    # Personal number model
    "PersonalNumber",
]
