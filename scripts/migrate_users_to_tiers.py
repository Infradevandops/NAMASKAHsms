#!/usr/bin/env python3
"""Migrate existing users to subscription tiers based on usage history."""

# Add parent directory to path

import sys
from pathlib import Path
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification

sys.path.insert(0, str(Path(__file__).parent.parent))


def migrate_users_to_tiers():

    """Assign tiers to existing users based on usage patterns."""
    db = next(get_db())

try:
        users = db.query(User).all()
        print(f"Found {len(users)} users to migrate")

for user in users:
            # Skip if already has a tier assigned (not default)
if user.subscription_tier and user.subscription_tier != "freemium":
                print(f"User {user.email} already has tier: {user.subscription_tier}")
                continue

            # Count verifications in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
try:
                recent_verifications = (
                    db.query(Verification)
                    .filter(
                        Verification.user_id == user.id,
                        Verification.created_at >= thirty_days_ago,
                    )
                    .count()
                )
except Exception:
                recent_verifications = 0

            # Determine tier based on usage and admin status
if user.is_admin:
                new_tier = "turbo"
                reason = "Admin user"
elif recent_verifications > 500:
                new_tier = "starter"
                reason = f"High usage ({recent_verifications} verifications)"
else:
                new_tier = "freemium"
                reason = f"Standard user ({recent_verifications} verifications)"

            # Update user
            user.subscription_tier = new_tier
            print(f"✓ {user.email} → {new_tier} ({reason})")

        db.commit()
        print(f"\n✅ Successfully migrated {len(users)} users")

except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {str(e)}")
        raise
finally:
        db.close()


if __name__ == "__main__":
    print("Starting user tier migration...")
    migrate_users_to_tiers()
    print("Migration complete!")
