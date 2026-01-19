#!/usr/bin/env python3
"""
Distribute existing users across all 4 tiers
Spreads users evenly for testing purposes
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text


def distribute_users_across_tiers():
    """Distribute existing users across all 4 tiers"""

    db = next(get_db())

    print("🔄 Distributing users across all tiers...")

    # Get all users
    users = db.execute(
        text("SELECT id, email FROM users ORDER BY created_at")
    ).fetchall()

    if not users:
        print("❌ No users found in database")
        return

    total_users = len(users)
    print(f"📊 Found {total_users} users")

    # Define tier distribution
    tiers = ["freemium", "payg", "pro", "custom"]

    # Distribute users evenly across tiers
    for idx, user in enumerate(users):
        tier = tiers[idx % len(tiers)]  # Round-robin distribution

        db.execute(
            text(
                """
            UPDATE users 
            SET subscription_tier = :tier, tier_id = :tier
            WHERE id = :user_id
        """
            ),
            {"tier": tier, "user_id": user[0]},
        )

        print(f"   ✅ {user[1][:30]} → {tier}")

    db.commit()

    # Show final distribution
    print("\n📊 Final tier distribution:")
    distribution = db.execute(
        text(
            """
        SELECT subscription_tier, COUNT(*) as count 
        FROM users 
        GROUP BY subscription_tier
        ORDER BY 
            CASE subscription_tier
                WHEN 'freemium' THEN 1
                WHEN 'payg' THEN 2
                WHEN 'pro' THEN 3
                WHEN 'custom' THEN 4
            END
    """
        )
    ).fetchall()

    for tier, count in distribution:
        percentage = (count / total_users) * 100
        print(f"   {tier.upper()}: {count} users ({percentage:.1f}%)")

    db.close()

    print("\n✅ Users successfully distributed across all tiers!")
    print("\n💡 Distribution pattern:")
    print("   User 1 → Freemium")
    print("   User 2 → Pay-As-You-Go")
    print("   User 3 → Pro")
    print("   User 4 → Custom")
    print("   User 5 → Freemium (cycle repeats)")


if __name__ == "__main__":
    print("🎯 Distributing users across all 4 tiers...\n")
    distribute_users_across_tiers()
