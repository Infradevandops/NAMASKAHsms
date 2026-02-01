"""Process refunds for verifications that were charged but never received SMS."""


import os
import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logger = get_logger(__name__)


def find_unreceived_verifications(db, days_back=7, min_age_minutes=10):

    """Find verifications that were charged but never received SMS.

    Args:
        db: Database session
        days_back: How many days to look back
        min_age_minutes: Minimum age for pending verifications

    Returns:
        List of verification records needing refund
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
    pending_cutoff = datetime.now(timezone.utc) - timedelta(minutes=min_age_minutes)

    # Find verifications that should be refunded
    unreceived = (
        db.query(Verification)
        .filter(
            and_(
                Verification.cost > 0,
                Verification.sms_code.is_(None),
                Verification.created_at > cutoff_time,
                or_(
                    # Pending too long
                    and_(
                        Verification.status == "pending",
                        Verification.created_at < pending_cutoff,
                    ),
                    # Failed/error status
                    Verification.status.in_(["failed", "error", "cancelled"]),
                ),
            )
        )
        .all()
    )

    # Filter out already refunded
    needs_refund = []
for verification in unreceived:
        # Check if refund already exists
        existing_refund = (
            db.query(Transaction)
            .filter(
                and_(
                    Transaction.user_id == verification.user_id,
                    Transaction.transaction_type == "refund",
                    Transaction.created_at > verification.created_at,
                    Transaction.amount == verification.cost,
                )
            )
            .first()
        )

if not existing_refund:
            needs_refund.append(verification)

    return needs_refund


def process_refund(db, verification, dry_run=True):

    """Process refund for a single verification.

    Args:
        db: Database session
        verification: Verification record
        dry_run: If True, don't commit changes

    Returns:
        bool: Success status
    """
try:
        user = db.query(User).filter(User.id == verification.user_id).first()
if not user:
            logger.error(f"User not found for verification {verification.id}")
            return False

        refund_amount = verification.cost

        # Determine refund reason
if verification.status == "pending":
            reason = "Timeout refund - No SMS received after 10+ minutes"
elif verification.status == "cancelled":
            reason = "Cancellation refund"
else:
            reason = f"Failure refund - Status: {verification.status}"

        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Refunding ${refund_amount:.2f} to user {user.email}"
        )
        logger.info(f"  Verification ID: {verification.id}")
        logger.info(f"  Service: {verification.service_name}")
        logger.info(f"  Reason: {reason}")

if not dry_run:
            # Create refund transaction
            transaction = Transaction(
                user_id=user.id,
                amount=refund_amount,
                transaction_type="refund",
                status="completed",
                description=f"Refund for verification {verification.id[:8]} - {reason}",
                metadata={
                    "verification_id": verification.id,
                    "service_name": verification.service_name,
                    "original_cost": float(refund_amount),
                    "refund_reason": reason,
                },
            )
            db.add(transaction)

            # Credit user account
            user.credits += refund_amount

            # Update verification status
if verification.status == "pending":
                verification.status = "timeout"

            db.commit()
            logger.info("✅ Refund processed successfully")

        return True

except Exception as e:
        logger.error(f"Failed to process refund for {verification.id}: {e}")
        db.rollback()
        return False


def generate_report(verifications):

    """Generate summary report of refunds.

    Args:
        verifications: List of verification records

    Returns:
        dict: Summary statistics
    """
if not verifications:
        return {
            "total_count": 0,
            "total_amount": 0,
            "affected_users": 0,
            "by_service": {},
            "by_status": {},
        }

    total_amount = sum(v.cost for v in verifications)
    affected_users = len(set(v.user_id for v in verifications))

    by_service = {}
    by_status = {}

for v in verifications:
        # By service
if v.service_name not in by_service:
            by_service[v.service_name] = {"count": 0, "amount": 0}
        by_service[v.service_name]["count"] += 1
        by_service[v.service_name]["amount"] += v.cost

        # By status
if v.status not in by_status:
            by_status[v.status] = {"count": 0, "amount": 0}
        by_status[v.status]["count"] += 1
        by_status[v.status]["amount"] += v.cost

    return {
        "total_count": len(verifications),
        "total_amount": float(total_amount),
        "affected_users": affected_users,
        "by_service": by_service,
        "by_status": by_status,
    }


def main():

    """Main execution function."""

    parser = argparse.ArgumentParser(
        description="Process refunds for unreceived verifications"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Days to look back (default: 7)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually process refunds (default: dry run)",
    )
    parser.add_argument(
        "--min-age",
        type=int,
        default=10,
        help="Min age in minutes for pending (default: 10)",
    )

    args = parser.parse_args()

    db = SessionLocal()

try:
        logger.info(f"{'='*60}")
        logger.info("UNRECEIVED VERIFICATION REFUND AUDIT")
        logger.info(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
        logger.info(f"Looking back: {args.days} days")
        logger.info(f"Min age for pending: {args.min_age} minutes")
        logger.info(f"{'='*60}\n")

        # Find verifications needing refund
        verifications = find_unreceived_verifications(db, args.days, args.min_age)

if not verifications:
            logger.info("✅ No verifications found needing refund!")
            return

        # Generate report
        report = generate_report(verifications)

        logger.info("\n📊 REFUND SUMMARY:")
        logger.info(f"  Total verifications: {report['total_count']}")
        logger.info(f"  Total amount: ${report['total_amount']:.2f}")
        logger.info(f"  Affected users: {report['affected_users']}")

        logger.info("\n  By Service:")
for service, data in report["by_service"].items():
            logger.info(
                f"    {service}: {data['count']} verifications, ${data['amount']:.2f}"
            )

        logger.info("\n  By Status:")
for status, data in report["by_status"].items():
            logger.info(
                f"    {status}: {data['count']} verifications, ${data['amount']:.2f}"
            )

        logger.info(f"\n{'='*60}")

        # Process refunds
        success_count = 0
for verification in verifications:
if process_refund(db, verification, dry_run=not args.execute):
                success_count += 1

        logger.info(f"\n{'='*60}")
        logger.info("RESULTS:")
        logger.info(f"  Processed: {success_count}/{len(verifications)}")

if not args.execute:
            logger.info("\n⚠️  This was a DRY RUN - no changes made")
            logger.info("  Run with --execute to process refunds")
else:
            logger.info("\n✅ Refunds processed successfully")

finally:
        db.close()


if __name__ == "__main__":
    main()