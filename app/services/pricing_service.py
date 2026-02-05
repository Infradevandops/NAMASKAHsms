"""Pricing Service for SMS Verification."""


from app.models.user import User

class PricingService:

    """Calculate SMS verification pricing with premiums and discounts."""

    BASE_PRICES = {
        "whatsapp": 2.22,
        "telegram": 1.80,
        "discord": 2.50,
        "google": 2.00,
        "facebook": 2.10,
        "twitter": 2.30,
        "instagram": 2.40,
        "tiktok": 2.50,
        "snapchat": 2.20,
        "uber": 2.60,
        "lyft": 2.60,
        "default": 2.50,
    }

    AREA_CODE_PREMIUMS = {
        "212": 0.50,  # NYC
        "917": 0.50,  # NYC
        "310": 0.50,  # LA
        "415": 0.50,  # SF
        "312": 0.40,  # Chicago
        "404": 0.40,  # Atlanta
        "617": 0.40,  # Boston
        "702": 0.30,  # Las Vegas
    }

    CARRIER_PREMIUMS = {
        "tmobile": 0.25,
        "t-mobile": 0.25,
        "verizon": 0.30,
        "att": 0.20,
        "at&t": 0.20,
        "sprint": 0.20,
    }

    TIER_DISCOUNTS = {
        "freemium": 0.0,
        "payg": 0.0,
        "pro": 0.15,  # 15% discount
        "custom": 0.25,  # 25% discount
    }

    def calculate_price(

        self,
        service: str,
        user: User,
        area_code: str = None,
        carrier: str = None,
        ) -> dict:
        """Calculate total price with all premiums and discounts.

        Args:
            service: Service name (e.g., 'whatsapp')
            user: User object with tier information
            area_code: Optional area code (e.g., '212')
            carrier: Optional carrier (e.g., 'tmobile')

        Returns:
            Dict with pricing breakdown
        """
        # Get base price
        base_price = self.BASE_PRICES.get(service.lower(), self.BASE_PRICES["default"])

        # Calculate area code premium
        area_premium = 0.0
        if area_code and area_code in self.AREA_CODE_PREMIUMS:
            area_premium = self.AREA_CODE_PREMIUMS[area_code]

        # Calculate carrier premium
        carrier_premium = 0.0
        if carrier and carrier.lower() in self.CARRIER_PREMIUMS:
            carrier_premium = self.CARRIER_PREMIUMS[carrier.lower()]

        # Calculate subtotal
        subtotal = base_price + area_premium + carrier_premium

        # Apply tier discount
        tier = user.tier if hasattr(user, "tier") else "freemium"
        discount_rate = self.TIER_DISCOUNTS.get(tier, 0.0)
        discount_amount = subtotal * discount_rate

        # Calculate final total
        total = subtotal - discount_amount

        return {
            "base_price": round(base_price, 2),
            "area_code_premium": round(area_premium, 2),
            "carrier_premium": round(carrier_premium, 2),
            "subtotal": round(subtotal, 2),
            "discount_rate": discount_rate,
            "discount_amount": round(discount_amount, 2),
            "total_price": round(total, 2),
            "currency": "USD",
            "tier": tier,
        }
