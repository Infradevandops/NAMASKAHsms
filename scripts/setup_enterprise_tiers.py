"""Setup default enterprise tiers."""


from app.core.database import SessionLocal
from app.models.enterprise import EnterpriseTier

def setup_default_tiers():

    """Create default enterprise tiers."""
    db = SessionLocal()

    tiers = [
        {
            "name": "Business",
            "min_monthly_spend": 100.0,
            "sla_uptime": 99.5,
            "max_response_time": 3000,
            "priority_support": True,
            "dedicated_manager": False,
            "features": {
                "api_rate_limit": 2000,
                "webhook_retries": 5,
                "analytics_retention": 180,
            },
        },
        {
            "name": "Enterprise",
            "min_monthly_spend": 500.0,
            "sla_uptime": 99.9,
            "max_response_time": 2000,
            "priority_support": True,
            "dedicated_manager": True,
            "features": {
                "api_rate_limit": 5000,
                "webhook_retries": 10,
                "analytics_retention": 365,
            },
        },
        {
            "name": "Premium",
            "min_monthly_spend": 1000.0,
            "sla_uptime": 99.95,
            "max_response_time": 1000,
            "priority_support": True,
            "dedicated_manager": True,
            "features": {
                "api_rate_limit": 10000,
                "webhook_retries": 15,
                "analytics_retention": 730,
            },
        },
    ]

for tier_data in tiers:
        existing = (
            db.query(EnterpriseTier)
            .filter(EnterpriseTier.name == tier_data["name"])
            .first()
        )

if not existing:
            tier = EnterpriseTier(**tier_data)
            db.add(tier)

    db.commit()
    db.close()
    print("Enterprise tiers setup complete!")


if __name__ == "__main__":
    setup_default_tiers()