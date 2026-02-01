#!/usr/bin/env python3
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.tier_config import TierConfig
from app.models.user import User

Tier Management CLI Tool
Manage user subscription tiers from command line
"""


logger = get_logger(__name__)


def get_db():

    """Get database session."""
    return SessionLocal()


def list_tiers(db: Session):

    """List all available tiers."""
    print("\n📊 Available Tiers:")
    print("-" * 80)

    tiers = TierConfig.get_all_tiers(db)
for tier in tiers:
        print(f"\n  {tier['name'].upper()}")
        print(f"    Price: ${tier['price_monthly']/100:.2f}/month")
        print(f"    Quota: ${tier['quota_usd']}")
        print(
            f"    API Keys: {tier['api_key_limit'] if tier['api_key_limit'] != -1 else 'Unlimited'}"
        )
        print("    Features:")
        print(f"      - API Access: {'✓' if tier['has_api_access'] else '✗'}")
        print(
            f"      - Area Code Selection: {'✓' if tier['has_area_code_selection'] else '✗'}"
        )
        print(f"      - ISP Filtering: {'✓' if tier['has_isp_filtering'] else '✗'}")


def list_users(db: Session, tier: str = None, limit: int = 20):

    """List users, optionally filtered by tier."""
    query = db.query(User)

if tier:
        query = query.filter(User.subscription_tier == tier)

    users = query.order_by(User.created_at.desc()).limit(limit).all()

    print(f"\n👥 Users ({len(users)} shown):")
    print("-" * 100)
    print(f"{'Email':<30} {'Tier':<12} {'Expires':<15} {'Credits':<10} {'Joined':<12}")
    print("-" * 100)

for user in users:
        tier_name = user.subscription_tier or "freemium"
        expires = (
            user.tier_expires_at.strftime("%Y-%m-%d") if user.tier_expires_at else "N/A"
        )
        created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"

        print(
            f"{user.email:<30} {tier_name:<12} {expires:<15} ${user.credits:<9.2f} {created:<12}"
        )


def set_user_tier(db: Session, user_id: str, tier: str, days: int = 30):

    """Set user tier."""
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        print(f"❌ User {user_id} not found")
        return False

    valid_tiers = ["freemium", "payg", "pro", "custom"]
if tier not in valid_tiers:
        print(f"❌ Invalid tier: {tier}. Must be one of: {', '.join(valid_tiers)}")
        return False

    old_tier = user.subscription_tier or "freemium"
    user.subscription_tier = tier

if tier != "freemium":
        user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=days)
else:
        user.tier_expires_at = None

    db.commit()

    expires_str = (
        user.tier_expires_at.strftime("%Y-%m-%d") if user.tier_expires_at else "Never"
    )
    print(f"✅ User {user.email} tier updated: {old_tier} → {tier}")
    print(f"   Expires: {expires_str}")

    return True


def bulk_set_tier(db: Session, user_ids: list, tier: str, days: int = 30):

    """Set tier for multiple users."""
    valid_tiers = ["freemium", "payg", "pro", "custom"]
if tier not in valid_tiers:
        print(f"❌ Invalid tier: {tier}")
        return False

    users = db.query(User).filter(User.id.in_(user_ids)).all()
if not users:
        print("❌ No users found")
        return False

    updated = 0
for user in users:
        user.subscription_tier = tier
if tier != "freemium":
            user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=days)
else:
            user.tier_expires_at = None
        updated += 1

    db.commit()
    print(f"✅ Updated {updated} users to {tier} tier")

    return True


def get_user_info(db: Session, user_id: str):

    """Get detailed user information."""
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        print(f"❌ User {user_id} not found")
        return False

    tier = user.subscription_tier or "freemium"
    tier_config = TierConfig.get_tier_config(tier, db)

    print("\n📋 User Information:")
    print("-" * 50)
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Tier: {tier.upper()}")
    print(f"  Tier Name: {tier_config['name']}")
    print(f"  Credits: ${user.credits:.2f}")
    print(f"  Admin: {'Yes' if user.is_admin else 'No'}")
    print(
        f"  Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}"
    )
    print(
        f"  Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'}"
    )

if user.tier_expires_at:
        expires = user.tier_expires_at.strftime("%Y-%m-%d %H:%M:%S")
        is_expired = user.tier_expires_at < datetime.now(timezone.utc)
        print(f"  Tier Expires: {expires} {'(EXPIRED)' if is_expired else ''}")
else:
        print("  Tier Expires: Never")

    print("\n  Tier Features:")
    print(f"    - API Access: {'✓' if tier_config['has_api_access'] else '✗'}")
    print(
        f"    - Area Code Selection: {'✓' if tier_config['has_area_code_selection'] else '✗'}"
    )
    print(f"    - ISP Filtering: {'✓' if tier_config['has_isp_filtering'] else '✗'}")
    print(
        f"    - API Key Limit: {tier_config['api_key_limit'] if tier_config['api_key_limit'] != -1 else 'Unlimited'}"
    )

    return True


def extend_tier(db: Session, user_id: str, days: int = 30):

    """Extend user tier expiry."""
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        print(f"❌ User {user_id} not found")
        return False

    tier = user.subscription_tier or "freemium"
if tier == "freemium":
        print("❌ Cannot extend Freemium tier")
        return False

    old_expiry = user.tier_expires_at
if user.tier_expires_at:
        user.tier_expires_at = user.tier_expires_at + timedelta(days=days)
else:
        user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    db.commit()

    print(f"✅ Tier extended by {days} days")
if old_expiry:
        print(f"   Old expiry: {old_expiry.strftime('%Y-%m-%d')}")
    print(f"   New expiry: {user.tier_expires_at.strftime('%Y-%m-%d')}")

    return True


def get_expiring_tiers(db: Session, days: int = 7):

    """Get users with tiers expiring soon."""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days)

    users = (
        db.query(User)
        .filter(
            User.tier_expires_at.isnot(None),
            User.tier_expires_at >= now,
            User.tier_expires_at <= future,
        )
        .order_by(User.tier_expires_at)
        .all()
    )

    print(f"\n⏰ Tiers Expiring in {days} Days ({len(users)} users):")
    print("-" * 100)
    print(f"{'Email':<30} {'Tier':<12} {'Expires':<15} {'Days Left':<12}")
    print("-" * 100)

for user in users:
        tier_name = user.subscription_tier or "freemium"
        expires = user.tier_expires_at.strftime("%Y-%m-%d")
        days_left = (user.tier_expires_at - now).days

        print(f"{user.email:<30} {tier_name:<12} {expires:<15} {days_left:<12}")


def main():

    parser = argparse.ArgumentParser(
        description="Namaskah Tier Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available tiers
  python tier_cli.py list-tiers

  # List users
  python tier_cli.py list-users --tier starter --limit 50

  # Get user info
  python tier_cli.py user-info <user_id>

  # Set user tier
  python tier_cli.py set-tier <user_id> pro --days 30

  # Extend tier
  python tier_cli.py extend-tier <user_id> --days 30

  # Get expiring tiers
  python tier_cli.py expiring --days 7
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List tiers
    subparsers.add_parser("list-tiers", help="List all available tiers")

    # List users
    list_users_parser = subparsers.add_parser("list-users", help="List users")
    list_users_parser.add_argument("--tier", help="Filter by tier")
    list_users_parser.add_argument(
        "--limit", type=int, default=20, help="Number of users to show"
    )

    # User info
    user_info_parser = subparsers.add_parser("user-info", help="Get user information")
    user_info_parser.add_argument("user_id", help="User ID")

    # Set tier
    set_tier_parser = subparsers.add_parser("set-tier", help="Set user tier")
    set_tier_parser.add_argument("user_id", help="User ID")
    set_tier_parser.add_argument(
        "tier", choices=["freemium", "payg", "pro", "custom"], help="Tier name"
    )
    set_tier_parser.add_argument(
        "--days", type=int, default=30, help="Duration in days"
    )

    # Bulk set tier
    bulk_parser = subparsers.add_parser(
        "bulk-set-tier", help="Set tier for multiple users"
    )
    bulk_parser.add_argument("user_ids", nargs="+", help="User IDs")
    bulk_parser.add_argument(
        "tier", choices=["freemium", "payg", "pro", "custom"], help="Tier name"
    )
    bulk_parser.add_argument("--days", type=int, default=30, help="Duration in days")

    # Extend tier
    extend_parser = subparsers.add_parser("extend-tier", help="Extend user tier")
    extend_parser.add_argument("user_id", help="User ID")
    extend_parser.add_argument("--days", type=int, default=30, help="Days to extend")

    # Expiring tiers
    expiring_parser = subparsers.add_parser("expiring", help="Get expiring tiers")
    expiring_parser.add_argument("--days", type=int, default=7, help="Days threshold")

    args = parser.parse_args()

if not args.command:
        parser.print_help()
        return

    db = get_db()

try:
if args.command == "list-tiers":
            list_tiers(db)

elif args.command == "list-users":
            list_users(db, args.tier, args.limit)

elif args.command == "user-info":
            get_user_info(db, args.user_id)

elif args.command == "set-tier":
            set_user_tier(db, args.user_id, args.tier, args.days)

elif args.command == "bulk-set-tier":
            bulk_set_tier(db, args.user_ids, args.tier, args.days)

elif args.command == "extend-tier":
            extend_tier(db, args.user_id, args.days)

elif args.command == "expiring":
            get_expiring_tiers(db, args.days)

except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

finally:
        db.close()


if __name__ == "__main__":
    main()