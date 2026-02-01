"""Pricing display utilities for frontend."""


def format_pricing_breakdown(breakdown: dict) -> dict:

    """Format pricing breakdown for display."""
    return {
        "tier": breakdown["tier"],
        "tier_name": breakdown["tier_name"],
        "base_cost": f"${breakdown['base_cost']:.2f}",
        "filter_charges": f"${breakdown['filter_charges']:.2f}",
        "overage_charge": f"${breakdown['overage_charge']:.2f}",
        "total_cost": f"${breakdown['total_cost']:.2f}",
        "quota_limit": f"${breakdown['quota_limit']:.2f}",
        "quota_used": f"${breakdown['quota_used']:.2f}",
        "quota_remaining": f"${breakdown['quota_remaining']:.2f}",
        "user_balance": f"${breakdown['user_balance']:.2f}",
        "bonus_sms": int(breakdown["bonus_sms"]),
        "sufficient_balance": breakdown["sufficient_balance"],
    }


def get_quota_percentage(quota_used: float, quota_limit: float) -> int:

    """Calculate quota usage percentage."""
if quota_limit == 0:
        return 0
    return min(100, int((quota_used / quota_limit) * 100))


def format_quota_status(quota_used: float, quota_limit: float) -> str:

    """Format quota status message."""
if quota_limit == 0:
        return "No quota limit"
    remaining = quota_limit - quota_used
if remaining <= 0:
        return "Quota exceeded - overage charges apply"
    return f"${remaining:.2f} remaining"