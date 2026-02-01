#!/usr/bin/env python3
"""
import argparse
import sys
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.auto_refund_service import AutoRefundService
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction

Refund Reconciliation Script
=============================
Identifies and refunds users affected by the verification refund bug.

Usage:
    # Dry run (report only)
    python reconcile_refunds.py --dry-run

    # Process refunds
    python reconcile_refunds.py --execute

    # Check specific user
    python reconcile_refunds.py --user-id USER_ID

    # Check last N days
    python reconcile_refunds.py --days 7 --dry-run
"""


logger = get_logger(__name__)


def main():

    parser = argparse.ArgumentParser(
        description="Refund reconciliation for failed verifications"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report only, don't process refunds",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Process refunds (use with caution)",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Check specific user only",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )

    args = parser.parse_args()

if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)

if args.dry_run and args.execute:
        print("ERROR: Cannot use both --dry-run and --execute")
        sys.exit(1)

    db = SessionLocal()

try:
        refund_service = AutoRefundService(db)

        print("=" * 80)
        print("REFUND RECONCILIATION REPORT")
        print("=" * 80)
        print(
            f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'EXECUTE (processing refunds)'}"
        )
        print(f"Days back: {args.days}")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 80)
        print()

if args.user_id:
            # Check specific user

            user = db.query(User).filter(User.id == args.user_id).first()
if not user:
                print(f"ERROR: User {args.user_id} not found")
                sys.exit(1)

            print(f"User: {user.email} (ID: {user.id})")
            print(f"Current Balance: ${user.credits:.2f}")
            print(f"Tier: {user.subscription_tier}")
            print()

            verifications = (
                db.query(Verification)
                .filter(
                    Verification.user_id == args.user_id,
                    Verification.status.in_(["timeout", "cancelled", "failed"]),
                )
                .all()
            )

            print(f"Failed Verifications: {len(verifications)}")
            print("-" * 80)

            total_refund = 0.0
for v in verifications:

                existing_refund = (
                    db.query(Transaction)
                    .filter(
                        Transaction.user_id == v.user_id,
                        Transaction.type == "verification_refund",
                        Transaction.description.contains(v.id),
                    )
                    .first()
                )

                status = "✓ Already Refunded" if existing_refund else "✗ Needs Refund"
                print(
                    f"{v.id} | {v.service_name} | ${v.cost:.2f} | {v.status} | {status}"
                )

if not existing_refund:
                    total_refund += v.cost

            print("-" * 80)
            print(f"Total Refund Due: ${total_refund:.2f}")
            print()

if not args.dry_run and total_refund > 0:
                confirm = input(
                    f"Process ${total_refund:.2f} refund for user {user.email}? (yes/no): "
                )
if confirm.lower() == "yes":
for v in verifications:
                        result = refund_service.process_verification_refund(
                            v.id, v.status
                        )
if result:
                            print(
                                f"✓ Refunded ${result['refund_amount']:.2f} for {v.id}"
                            )
                    print("\n✓ Refunds processed successfully")
else:
                    print("Cancelled")

else:
            # Full reconciliation
            report = refund_service.reconcile_unrefunded_verifications(
                days_back=args.days,
                dry_run=args.dry_run,
            )

            print("SUMMARY:")
            print("-" * 80)
            print(f"Total Failed Verifications: {report['total_failed']}")
            print(f"Already Refunded: {report['already_refunded']}")
            print(f"Needs Refund: {report['needs_refund']}")
            print(f"Refunded Now: {report['refunded_now']}")
            print(f"Errors: {report['refund_errors']}")
            print(f"Total Amount Refunded: ${report['total_amount_refunded']:.2f}")
            print()

if report["verifications"]:
                print("DETAILS:")
                print("-" * 80)
for v in report["verifications"]:
                    status = "✓ Refunded" if v.get("refunded") else "✗ Pending"
                    print(
                        f"{v['id'][:8]}... | {v['user_id'][:8]}... | "
                        f"{v['service']:15} | ${v['cost']:6.2f} | "
                        f"{v['status']:10} | {status}"
                    )
                print()

if args.dry_run and report["needs_refund"] > 0:
                print("=" * 80)
                print("⚠️  DRY RUN MODE - No refunds processed")
                print(f"Run with --execute to process {report['needs_refund']} refunds")
                print(
                    f"Total amount: ${sum(v['cost'] for v in report['verifications'] if not v.get('refunded')):.2f}"
                )
                print("=" * 80)

except Exception as e:
        logger.error(f"Reconciliation error: {str(e)}", exc_info=True)
        print(f"\nERROR: {str(e)}")
        sys.exit(1)
finally:
        db.close()


if __name__ == "__main__":
    main()
