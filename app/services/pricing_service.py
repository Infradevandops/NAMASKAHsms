"""Pricing service for managing pricing tiers and calculations."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)


class PricingService:
    """Service for managing pricing tiers and cost calculations."""

    # Pricing tier definitions
    TIERS = {
        "BASIC": {
            "name": "BASIC",
            "display_name": "Basic",
            "monthly_price": 0.0,
            "max_verifications_per_day": 5,
            "priority_number_access": 0.0,  # 0%
            "expedited_delivery_available": False,
            "ultra_fast_delivery_available": False,
            "api_rate_limit": 10,  # requests per minute
            "support_level": "email",
            "bulk_operations_limit": 0,
            "webhook_support": False,
            "analytics_level": "basic",
            "sla_uptime": 99.0,
        },
        "STANDARD": {
            "name": "STANDARD",
            "display_name": "Standard",
            "monthly_price": 10.0,
            "max_verifications_per_day": -1,  # unlimited
            "priority_number_access": 0.10,  # 10%
            "expedited_delivery_available": False,
            "ultra_fast_delivery_available": False,
            "api_rate_limit": 100,
            "support_level": "email",
            "bulk_operations_limit": 0,
            "webhook_support": False,
            "analytics_level": "basic",
            "sla_uptime": 99.5,
        },
        "PREMIUM": {
            "name": "PREMIUM",
            "display_name": "Premium",
            "monthly_price": 50.0,
            "max_verifications_per_day": -1,  # unlimited
            "priority_number_access": 0.50,  # 50%
            "expedited_delivery_available": True,
            "ultra_fast_delivery_available": True,
            "api_rate_limit": 1000,
            "support_level": "priority_email",
            "bulk_operations_limit": 50,
            "webhook_support": True,
            "analytics_level": "advanced",
            "sla_uptime": 99.9,
        },
        "ENTERPRISE": {
            "name": "ENTERPRISE",
            "display_name": "Enterprise",
            "monthly_price": 200.0,
            "max_verifications_per_day": -1,  # unlimited
            "priority_number_access": 1.0,  # 100%
            "expedited_delivery_available": True,
            "ultra_fast_delivery_available": True,
            "api_rate_limit": 10000,
            "support_level": "phone",
            "bulk_operations_limit": -1,  # unlimited
            "webhook_support": True,
            "analytics_level": "custom",
            "sla_uptime": 99.99,
        },
    }

    # Service costs (base cost per verification)
    SERVICE_COSTS = {
        "telegram": 0.20,
        "whatsapp": 0.30,
        "discord": 0.25,
        "twitter": 0.35,
        "instagram": 0.40,
        "facebook": 0.25,
        "google": 0.15,
        "amazon": 0.25,
        "uber": 0.30,
        "airbnb": 0.35,
    }

    # Country multipliers
    COUNTRY_MULTIPLIERS = {
        "US": 1.0,
        "UK": 1.1,
        "CA": 1.05,
        "AU": 1.15,
        "IN": 0.8,
        "BR": 0.9,
        "MX": 0.85,
        "RU": 0.75,
        "CN": 0.7,
        "JP": 1.2,
    }

    # Premium service surcharges
    PRIORITY_SURCHARGE = 0.50  # +$0.50 per verification
    ULTRA_FAST_SURCHARGE = 1.00  # +$1.00 per verification
    EXPEDITED_SURCHARGE = 0.25  # +$0.25 per verification

    # Tier discounts
    TIER_DISCOUNTS = {
        "BASIC": 0.0,
        "STANDARD": 0.0,
        "PREMIUM": 0.05,  # 5%
        "ENTERPRISE": 0.10,  # 10%
    }

    # Bulk discounts
    BULK_DISCOUNTS = {
        (5, 10): 0.05,  # 5% for 5-10
        (11, 25): 0.10,  # 10% for 11-25
        (26, 50): 0.15,  # 15% for 26-50
        (51, float("inf")): 0.20,  # 20% for 51+
    }

    def __init__(self, db: Session):
        """Initialize pricing service with database session."""
        self.db = db

    def get_tier(self, tier_name: str) -> Dict[str, Any]:
        """Get pricing tier details.
        
        Args:
            tier_name: Tier name (BASIC, STANDARD, PREMIUM, ENTERPRISE)
            
        Returns:
            Dictionary with tier details
            
        Raises:
            ValueError: If tier not found
        """
        tier_name = tier_name.upper()
        if tier_name not in self.TIERS:
            raise ValueError(f"Unknown tier: {tier_name}")
        
        return self.TIERS[tier_name]

    def get_all_tiers(self) -> List[Dict[str, Any]]:
        """Get all pricing tiers.
        
        Returns:
            List of tier dictionaries
        """
        return list(self.TIERS.values())

    def calculate_base_cost(
        self,
        service: str,
        country: str = "US"
    ) -> float:
        """Calculate base cost for a verification.
        
        Args:
            service: Service name (telegram, whatsapp, etc)
            country: Country code (default US)
            
        Returns:
            Base cost in USD
        """
        service = service.lower()
        country = country.upper()
        
        # Get service cost
        service_cost = self.SERVICE_COSTS.get(service, 0.25)
        
        # Get country multiplier
        country_multiplier = self.COUNTRY_MULTIPLIERS.get(country, 1.0)
        
        # Calculate base cost
        base_cost = service_cost * country_multiplier
        
        return round(base_cost, 2)

    def calculate_verification_cost(
        self,
        service: str,
        country: str = "US",
        tier: str = "STANDARD",
        quantity: int = 1,
        delivery_speed: str = "standard",
        use_priority_numbers: bool = False,
    ) -> Dict[str, Any]:
        """Calculate cost for verification(s).
        
        Args:
            service: Service name
            country: Country code
            tier: Pricing tier
            quantity: Number of verifications
            delivery_speed: standard, expedited, ultra_fast
            use_priority_numbers: Whether to use priority numbers
            
        Returns:
            Dictionary with cost breakdown
        """
        tier = tier.upper()
        if tier not in self.TIERS:
            raise ValueError(f"Unknown tier: {tier}")
        
        # Get base cost
        base_cost = self.calculate_base_cost(service, country)
        
        # Add delivery speed surcharge
        delivery_surcharge = 0.0
        if delivery_speed == "expedited":
            delivery_surcharge = self.EXPEDITED_SURCHARGE
        elif delivery_speed == "ultra_fast":
            delivery_surcharge = self.ULTRA_FAST_SURCHARGE
        
        # Add priority number surcharge
        priority_surcharge = 0.0
        if use_priority_numbers:
            priority_surcharge = self.PRIORITY_SURCHARGE
        
        # Calculate subtotal per unit
        subtotal_per_unit = base_cost + delivery_surcharge + priority_surcharge
        
        # Apply tier discount
        tier_discount = self.TIER_DISCOUNTS.get(tier, 0.0)
        discounted_cost_per_unit = subtotal_per_unit * (1 - tier_discount)
        
        # Apply bulk discount
        bulk_discount = self._get_bulk_discount(quantity)
        final_cost_per_unit = discounted_cost_per_unit * (1 - bulk_discount)
        
        # Calculate totals
        total_cost = final_cost_per_unit * quantity
        
        # Calculate savings
        original_cost = subtotal_per_unit * quantity
        total_savings = original_cost - total_cost
        
        return {
            "service": service,
            "country": country,
            "tier": tier,
            "quantity": quantity,
            "delivery_speed": delivery_speed,
            "use_priority_numbers": use_priority_numbers,
            "base_cost_per_unit": round(base_cost, 2),
            "delivery_surcharge": round(delivery_surcharge, 2),
            "priority_surcharge": round(priority_surcharge, 2),
            "subtotal_per_unit": round(subtotal_per_unit, 2),
            "tier_discount_percent": round(tier_discount * 100, 1),
            "tier_discount_amount": round(subtotal_per_unit * tier_discount, 2),
            "bulk_discount_percent": round(bulk_discount * 100, 1),
            "bulk_discount_amount": round(discounted_cost_per_unit * bulk_discount * quantity, 2),
            "final_cost_per_unit": round(final_cost_per_unit, 2),
            "total_cost": round(total_cost, 2),
            "original_cost": round(original_cost, 2),
            "total_savings": round(total_savings, 2),
            "savings_percent": round((total_savings / original_cost * 100) if original_cost > 0 else 0, 1),
        }

    def _get_bulk_discount(self, quantity: int) -> float:
        """Get bulk discount for quantity.
        
        Args:
            quantity: Number of items
            
        Returns:
            Discount percentage (0.0 to 1.0)
        """
        if quantity < 5:
            return 0.0
        
        for (min_qty, max_qty), discount in self.BULK_DISCOUNTS.items():
            if min_qty <= quantity <= max_qty:
                return discount
        
        return 0.0

    def get_tier_features(self, tier: str) -> Dict[str, Any]:
        """Get features for a tier.
        
        Args:
            tier: Tier name
            
        Returns:
            Dictionary with tier features
        """
        tier_data = self.get_tier(tier)
        
        return {
            "tier": tier,
            "display_name": tier_data["display_name"],
            "monthly_price": tier_data["monthly_price"],
            "features": {
                "max_verifications_per_day": tier_data["max_verifications_per_day"],
                "priority_number_access": f"{tier_data['priority_number_access'] * 100:.0f}%",
                "expedited_delivery": tier_data["expedited_delivery_available"],
                "ultra_fast_delivery": tier_data["ultra_fast_delivery_available"],
                "api_rate_limit": f"{tier_data['api_rate_limit']} req/min",
                "support_level": tier_data["support_level"],
                "bulk_operations_limit": tier_data["bulk_operations_limit"],
                "webhook_support": tier_data["webhook_support"],
                "analytics_level": tier_data["analytics_level"],
                "sla_uptime": f"{tier_data['sla_uptime']}%",
            },
        }

    def compare_tiers(self) -> List[Dict[str, Any]]:
        """Get comparison of all tiers.
        
        Returns:
            List of tier comparisons
        """
        return [self.get_tier_features(tier) for tier in self.TIERS.keys()]

    def get_addon_pricing(self) -> Dict[str, Any]:
        """Get pricing for add-on services.
        
        Returns:
            Dictionary with add-on pricing
        """
        return {
            "priority_numbers": {
                "name": "Priority Numbers",
                "cost": self.PRIORITY_SURCHARGE,
                "cost_type": "per_verification",
                "delivery_time": "5-15 seconds",
                "description": "Access to priority phone numbers with faster delivery",
            },
            "ultra_fast_numbers": {
                "name": "Ultra-Fast Numbers",
                "cost": self.ULTRA_FAST_SURCHARGE,
                "cost_type": "per_verification",
                "delivery_time": "1-5 seconds",
                "description": "Access to ultra-fast phone numbers with fastest delivery",
            },
            "expedited_delivery": {
                "name": "Expedited Delivery",
                "cost": self.EXPEDITED_SURCHARGE,
                "cost_type": "per_verification",
                "delivery_time": "5-15 seconds",
                "description": "Expedited SMS delivery service",
            },
            "number_reservation_24h": {
                "name": "24-Hour Number Reservation",
                "cost": 1.00,
                "cost_type": "per_number",
                "description": "Reserve a phone number for 24 hours",
            },
            "number_reservation_7d": {
                "name": "7-Day Number Reservation",
                "cost": 5.00,
                "cost_type": "per_number",
                "description": "Reserve a phone number for 7 days",
            },
            "number_reservation_30d": {
                "name": "30-Day Number Reservation",
                "cost": 15.00,
                "cost_type": "per_number",
                "description": "Reserve a phone number for 30 days",
            },
            "priority_email_support": {
                "name": "Priority Email Support",
                "cost": 10.00,
                "cost_type": "per_month",
                "response_time": "2-4 hours",
                "description": "Priority email support with faster response times",
            },
            "phone_support": {
                "name": "Phone Support",
                "cost": 50.00,
                "cost_type": "per_month",
                "response_time": "24/7",
                "description": "24/7 phone support",
            },
            "dedicated_manager": {
                "name": "Dedicated Account Manager",
                "cost": 200.00,
                "cost_type": "per_month",
                "description": "Dedicated account manager for enterprise support",
            },
        }

    def estimate_monthly_cost(
        self,
        tier: str,
        estimated_verifications_per_month: int = 100,
        avg_service: str = "telegram",
        avg_country: str = "US",
        use_priority_numbers_percent: float = 0.0,
    ) -> Dict[str, Any]:
        """Estimate monthly cost for a user.
        
        Args:
            tier: Pricing tier
            estimated_verifications_per_month: Estimated monthly verifications
            avg_service: Average service used
            avg_country: Average country
            use_priority_numbers_percent: Percentage using priority numbers
            
        Returns:
            Dictionary with monthly cost estimate
        """
        tier_data = self.get_tier(tier)
        
        # Subscription cost
        subscription_cost = tier_data["monthly_price"]
        
        # Verification costs
        verification_cost = 0.0
        if estimated_verifications_per_month > 0:
            # Calculate average verification cost
            cost_breakdown = self.calculate_verification_cost(
                service=avg_service,
                country=avg_country,
                tier=tier,
                quantity=estimated_verifications_per_month,
                use_priority_numbers=use_priority_numbers_percent > 0,
            )
            verification_cost = cost_breakdown["total_cost"]
        
        # Total monthly cost
        total_monthly_cost = subscription_cost + verification_cost
        
        return {
            "tier": tier,
            "subscription_cost": round(subscription_cost, 2),
            "estimated_verifications": estimated_verifications_per_month,
            "verification_cost": round(verification_cost, 2),
            "total_monthly_cost": round(total_monthly_cost, 2),
            "cost_per_verification": round(verification_cost / estimated_verifications_per_month, 2) if estimated_verifications_per_month > 0 else 0.0,
            "annual_cost": round(total_monthly_cost * 12, 2),
        }
