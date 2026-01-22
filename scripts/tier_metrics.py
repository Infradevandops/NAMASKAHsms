#!/usr/bin/env python3
from sqlalchemy import create_engine, text

from app.core.config import settings


def get_tier_distribution():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT subscription_tier, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM users
            GROUP BY subscription_tier
            ORDER BY count DESC
        """
            )
        )
        print("\n📊 Tier Distribution:")
        for row in result:
            print(f"  {row[0]:<12}: {row[1]:>5} ({row[2]:>5}%)")


if __name__ == "__main__":
    get_tier_distribution()
