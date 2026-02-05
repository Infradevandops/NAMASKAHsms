#!/usr/bin/env python3
"""
import argparse
import sys
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.user import User

Tier Field Migration Script

Migrates user tier data from deprecated `tier_id` field to canonical `subscription_tier` field.
This script consolidates tier information to ensure a single source of truth.

Usage:
    python scripts/migrate_tier_fields.py migrate     # Run migration
    python scripts/migrate_tier_fields.py verify      # Verify migration
    python scripts/migrate_tier_fields.py rollback    # Rollback migration
    python scripts/migrate_tier_fields.py --dry-run   # Preview changes without applying
"""


logger = get_logger(__name__)


def get_db() -> Session:

    """Get database session."""
    return SessionLocal()


def migrate_tier_fields(db: Session, dry_run: bool = False) -> Dict[str, Any]:

    """
    Migrate tier_id values to subscription_tier.

    Migration rules:
    1. If tier_id is not null and differs from 'freemium', copy to subscription_tier
    2. If tier_id is null, set subscription_tier to 'freemium'
    3. Skip users where subscription_tier already has a valid non-freemium value

    Args:
        db: Database session
        dry_run: If True, preview changes without applying

    Returns:
        Migration summary with counts
    """
    print("\n🔄 Starting Tier Field Migration...")
    print("-" * 60)

    # Get all users
    users = db.query(User).all()
    total_users = len(users)

    migrated_count = 0
    skipped_count = 0
    defaulted_count = 0
    errors = []

    migration_log = []

for user in users:
try:
            old_tier_id = getattr(user, "tier_id", None)
            current_subscription_tier = user.subscription_tier

            # Determine action
            action = None
            new_tier = None

if old_tier_id and old_tier_id != "freemium":
                # tier_id has a paid tier value
if (
                    not current_subscription_tier
                    or current_subscription_tier == "freemium"
                ):
                    # subscription_tier is empty or freemium, migrate the tier_id value
                    new_tier = old_tier_id
                    action = "migrate"
else:
                    # subscription_tier already has a value, skip
                    action = "skip"
elif not current_subscription_tier:
                # No tier_id and no subscription_tier, default to freemium
                new_tier = "freemium"
                action = "default"
else:
                # subscription_tier already set, skip
                action = "skip"

            # Apply changes
if action == "migrate":
                migration_log.append(
                    {
                        "user_id": user.id,
                        "email": user.email,
                        "old_tier_id": old_tier_id,
                        "old_subscription_tier": current_subscription_tier,
                        "new_subscription_tier": new_tier,
                        "action": "migrated",
                    }
                )
if not dry_run:
                    user.subscription_tier = new_tier
                migrated_count += 1
                print(f"  ✓ {user.email}: {old_tier_id} → {new_tier}")

elif action == "default":
                migration_log.append(
                    {
                        "user_id": user.id,
                        "email": user.email,
                        "old_tier_id": old_tier_id,
                        "old_subscription_tier": current_subscription_tier,
                        "new_subscription_tier": new_tier,
                        "action": "defaulted",
                    }
                )
if not dry_run:
                    user.subscription_tier = new_tier
                defaulted_count += 1
                print(f"  ○ {user.email}: NULL → freemium (default)")

else:
                skipped_count += 1

except Exception as e:
            errors.append({"user_id": user.id, "error": str(e)})
            logger.error(f"Error migrating user {user.id}: {e}")

    # Commit changes
if not dry_run and (migrated_count > 0 or defaulted_count > 0):
        db.commit()
        print("\n✅ Changes committed to database")
elif dry_run:
        print("\n⚠️  DRY RUN - No changes applied")

    # Summary
    summary = {
        "total_users": total_users,
        "migrated": migrated_count,
        "defaulted": defaulted_count,
        "skipped": skipped_count,
        "errors": len(errors),
        "dry_run": dry_run,
        "migration_log": migration_log,
    }

    print("\n" + "=" * 60)
    print("📊 Migration Summary:")
    print(f"   Total users:     {total_users}")
    print(f"   Migrated:        {migrated_count}")
    print(f"   Defaulted:       {defaulted_count}")
    print(f"   Skipped:         {skipped_count}")
    print(f"   Errors:          {len(errors)}")
    print("=" * 60)

if errors:
        print("\n❌ Errors:")
for err in errors:
            print(f"   User {err['user_id']}: {err['error']}")

    return summary


def verify_migration(db: Session) -> Dict[str, Any]:

    """
    Verify that migration was successful.

    Checks:
    1. All users have a subscription_tier value
    2. No users have NULL subscription_tier
    3. Tier distribution is reasonable

    Returns:
        Verification results
    """
    print("\n🔍 Verifying Migration...")
    print("-" * 60)

    users = db.query(User).all()
    total_users = len(users)

    null_tier_count = 0
    tier_distribution = {}
    issues = []

for user in users:
        tier = user.subscription_tier

if not tier:
            null_tier_count += 1
            issues.append(f"User {user.email} has NULL subscription_tier")
else:
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

    # Results
    success = null_tier_count == 0

    print("\n📊 Tier Distribution:")
for tier, count in sorted(tier_distribution.items()):
        percentage = (count / total_users * 100) if total_users > 0 else 0
        print(f"   {tier:<12}: {count:>5} ({percentage:.1f}%)")

    print(f"\n   Total users: {total_users}")
    print(f"   NULL tiers:  {null_tier_count}")

if success:
        print("\n✅ Migration verification PASSED")
else:
        print("\n❌ Migration verification FAILED")
for issue in issues[:10]:  # Show first 10 issues
            print(f"   - {issue}")
if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")

    return {
        "success": success,
        "total_users": total_users,
        "null_tier_count": null_tier_count,
        "tier_distribution": tier_distribution,
        "issues": issues,
    }


def rollback_migration(db: Session, dry_run: bool = False) -> Dict[str, Any]:

    """
    Rollback migration by copying subscription_tier back to tier_id.

    Note: This is a safety feature. In practice, you should remove tier_id
    column after confirming migration success.

    Args:
        db: Database session
        dry_run: If True, preview changes without applying

    Returns:
        Rollback summary
    """
    print("\n⏪ Rolling Back Migration...")
    print("-" * 60)

    users = db.query(User).all()
    total_users = len(users)

    rolled_back = 0
    skipped = 0

for user in users:
        subscription_tier = user.subscription_tier

if subscription_tier:
if not dry_run:
                # Copy subscription_tier back to tier_id if the attribute exists
if hasattr(user, "tier_id"):
                    user.tier_id = subscription_tier
            rolled_back += 1
            print(f"  ↩ {user.email}: tier_id = {subscription_tier}")
else:
            skipped += 1

if not dry_run and rolled_back > 0:
        db.commit()
        print("\n✅ Rollback committed to database")
elif dry_run:
        print("\n⚠️  DRY RUN - No changes applied")

    print("\n" + "=" * 60)
    print("📊 Rollback Summary:")
    print(f"   Total users:   {total_users}")
    print(f"   Rolled back:   {rolled_back}")
    print(f"   Skipped:       {skipped}")
    print("=" * 60)

    return {
        "total_users": total_users,
        "rolled_back": rolled_back,
        "skipped": skipped,
        "dry_run": dry_run,
    }


def main():

    parser = argparse.ArgumentParser(
        description="Migrate tier_id to subscription_tier field",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration (dry run)
  python scripts/migrate_tier_fields.py migrate --dry-run

  # Run actual migration
  python scripts/migrate_tier_fields.py migrate

  # Verify migration was successful
  python scripts/migrate_tier_fields.py verify

  # Rollback if needed
  python scripts/migrate_tier_fields.py rollback --dry-run
  python scripts/migrate_tier_fields.py rollback
        """,
    )

    parser.add_argument(
        "command", choices=["migrate", "verify", "rollback"], help="Command to execute"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )

    args = parser.parse_args()

    db = get_db()

try:
if args.command == "migrate":
            result = migrate_tier_fields(db, dry_run=args.dry_run)

elif args.command == "verify":
            result = verify_migration(db)

elif args.command == "rollback":
            result = rollback_migration(db, dry_run=args.dry_run)

        return 0 if result.get("success", True) else 1

except Exception as e:
        logger.error(f"Migration error: {e}")
        print(f"\n❌ Error: {e}")
        return 1

finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
