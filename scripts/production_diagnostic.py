#!/usr/bin/env python3
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy import desc, func
from app.core.database import SessionLocal
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
import traceback

Production Diagnostic Script
============================
Analyzes production database to assess refund issue impact.

Usage:
    python production_diagnostic.py
"""


# Check if production database URL is set
if not os.getenv("DATABASE_URL"):
    print("ERROR: DATABASE_URL environment variable not set")
    print("Set it to your production database connection string")
    sys.exit(1)


print("=" * 80)
print("PRODUCTION DIAGNOSTIC REPORT")
print("=" * 80)
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print(f"Database: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
print("=" * 80)
print()

db = SessionLocal()

try:
    # 1. Overall Statistics
    print("📊 OVERALL STATISTICS")
    print("-" * 80)

    total_users = db.query(func.count(User.id)).scalar()
    total_verifications = db.query(func.count(Verification.id)).scalar()
    total_transactions = db.query(func.count(Transaction.id)).scalar()

    print(f"Total Users: {total_users}")
    print(f"Total Verifications: {total_verifications}")
    print(f"Total Transactions: {total_transactions}")
    print()

    # 2. Verification Status Breakdown
    print("📱 VERIFICATION STATUS BREAKDOWN")
    print("-" * 80)

    status_counts = (
        db.query(Verification.status, func.count(Verification.id))
        .group_by(Verification.status)
        .all()
    )

for status, count in status_counts:
        percentage = (
            (count / total_verifications * 100) if total_verifications > 0 else 0
        )
        print(f"{status:15} : {count:6} ({percentage:5.1f}%)")
    print()

    # 3. Failed Verifications (Need Refund)
    print("🚨 FAILED VERIFICATIONS (POTENTIAL REFUNDS)")
    print("-" * 80)

    failed_statuses = ["timeout", "cancelled", "failed"]
    failed_verifications = (
        db.query(Verification).filter(Verification.status.in_(failed_statuses)).all()
    )

    print(f"Total Failed: {len(failed_verifications)}")

if failed_verifications:
        total_cost = sum(v.cost for v in failed_verifications)
        print(f"Total Cost: ${total_cost:.2f}")
        print()

        # Check which ones already have refunds
        refunded_count = 0
        unrefunded_count = 0
        unrefunded_amount = 0.0

for v in failed_verifications:
            existing_refund = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == v.user_id,
                    Transaction.type == "verification_refund",
                    Transaction.description.contains(v.id),
                )
                .first()
            )

if existing_refund:
                refunded_count += 1
else:
                unrefunded_count += 1
                unrefunded_amount += v.cost

        print(f"Already Refunded: {refunded_count}")
        print(f"Need Refund: {unrefunded_count}")
        print(f"Unrefunded Amount: ${unrefunded_amount:.2f}")
        print()

    # 4. Recent Verifications (Last 24 hours)
    print("🕐 LAST 24 HOURS")
    print("-" * 80)

    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_verifications = (
        db.query(Verification).filter(Verification.created_at >= yesterday).all()
    )

    print(f"Total Verifications: {len(recent_verifications)}")

if recent_verifications:
        recent_failed = [v for v in recent_verifications if v.status in failed_statuses]
        recent_completed = [v for v in recent_verifications if v.status == "completed"]

        print(f"Completed: {len(recent_completed)}")
        print(f"Failed: {len(recent_failed)}")

if len(recent_verifications) > 0:
            success_rate = len(recent_completed) / len(recent_verifications) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        print()

    # 5. Top 20 Recent Verifications
    print("📋 TOP 20 RECENT VERIFICATIONS")
    print("-" * 80)

    recent_20 = (
        db.query(Verification).order_by(desc(Verification.created_at)).limit(20).all()
    )

if recent_20:
        print(
            f"{'ID':<10} {'User':<10} {'Service':<15} {'Status':<12} {'Cost':<8} {'Created':<20}"
        )
        print("-" * 80)

for v in recent_20:
            created_str = (
                v.created_at.strftime("%Y-%m-%d %H:%M") if v.created_at else "N/A"
            )
            print(
                f"{v.id[:8]:<10} "
                f"{v.user_id[:8]:<10} "
                f"{v.service_name[:15]:<15} "
                f"{v.status:<12} "
                f"${v.cost:<7.2f} "
                f"{created_str:<20}"
            )
        print()

    # 6. Users with Failed Verifications
    print("👥 USERS WITH FAILED VERIFICATIONS")
    print("-" * 80)

if failed_verifications:
        user_failures = {}
for v in failed_verifications:
if v.user_id not in user_failures:
                user_failures[v.user_id] = {"count": 0, "amount": 0.0}
            user_failures[v.user_id]["count"] += 1
            user_failures[v.user_id]["amount"] += v.cost

        # Sort by amount
        sorted_users = sorted(
            user_failures.items(), key=lambda x: x[1]["amount"], reverse=True
        )[:10]

        print(
            f"{'User ID':<15} {'Email':<30} {'Failed':<8} {'Amount':<10} {'Balance':<10}"
        )
        print("-" * 80)

for user_id, data in sorted_users:
            user = db.query(User).filter(User.id == user_id).first()
            email = user.email if user else "N/A"
            balance = f"${user.credits:.2f}" if user else "N/A"

            print(
                f"{user_id[:13]:<15} "
                f"{email[:28]:<30} "
                f"{data['count']:<8} "
                f"${data['amount']:<9.2f} "
                f"{balance:<10}"
            )
        print()

    # 7. Transaction Analysis
    print("💰 TRANSACTION ANALYSIS")
    print("-" * 80)

    transaction_types = (
        db.query(
            Transaction.type, func.count(Transaction.id), func.sum(Transaction.amount)
        )
        .group_by(Transaction.type)
        .all()
    )

    print(f"{'Type':<20} {'Count':<10} {'Total Amount':<15}")
    print("-" * 80)

for tx_type, count, total in transaction_types:
        total_str = f"${total:.2f}" if total else "$0.00"
        print(f"{tx_type:<20} {count:<10} {total_str:<15}")
    print()

    # 8. Refund Transactions
    print("🔄 REFUND TRANSACTIONS")
    print("-" * 80)

    refund_transactions = (
        db.query(Transaction)
        .filter(Transaction.type.in_(["refund", "verification_refund"]))
        .order_by(desc(Transaction.created_at))
        .limit(10)
        .all()
    )

if refund_transactions:
        print(f"Total Refund Transactions: {len(refund_transactions)}")
        print()
        print(f"{'ID':<10} {'User':<10} {'Amount':<10} {'Description':<40}")
        print("-" * 80)

for tx in refund_transactions:
            print(
                f"{tx.id[:8]:<10} "
                f"{tx.user_id[:8]:<10} "
                f"${tx.amount:<9.2f} "
                f"{tx.description[:38]:<40}"
            )
else:
        print("⚠️  NO REFUND TRANSACTIONS FOUND")
        print("This confirms the bug - failed verifications have NOT been refunded!")
    print()

    # 9. Critical Issues Summary
    print("🚨 CRITICAL ISSUES SUMMARY")
    print("=" * 80)

if unrefunded_count > 0:
        print(f"❌ {unrefunded_count} verifications need refunds")
        print(f"❌ ${unrefunded_amount:.2f} in unrefunded charges")
        print(f"❌ {len(user_failures)} users affected")
        print()
        print("ACTION REQUIRED:")
        print("1. Run: python reconcile_refunds.py --dry-run")
        print("2. Review the report")
        print("3. Run: python reconcile_refunds.py --execute")
else:
        print("✅ No unrefunded verifications found")
        print("✅ System is working correctly")

    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")

    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

print("\nDiagnostic complete.")