"""
Institutional Wallet Reconciliation Script (Brutal Stability)
Scans for unrefunded terminal failures (failed/timeout/cancelled) and processes refunds.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone

# Add parent directory to path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Force fallback allowance for CLI operations in non-primary environments
os.environ['ALLOW_SQLITE_FALLBACK'] = 'true'
os.environ['ENVIRONMENT'] = 'development' # Ensure we don't hit production constraints locally

from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction, PaymentLog # Fix: Combined module
from app.models.balance_transaction import BalanceTransaction
from app.models.activity import Activity # Fix: Needed for registry resolution
from app.services.auto_refund_service import AutoRefundService # Restore missing import

from app.core.database import SessionLocal, create_tables
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("reconcile")

async def run_reconciliation(days_back: int = 30, dry_run: bool = True):
    # Ensure tables exist in the current environment/fallback
    create_tables()
    
    db = SessionLocal()
    try:
        logger.info(f"Starting Financial Reconciliation (Days Back: {days_back}, Dry Run: {dry_run})")
        
        refund_service = AutoRefundService(db)
        report = refund_service.reconcile_unrefunded_verifications(
            days_back=days_back,
            dry_run=dry_run
        )
        
        print("\n=== RECONCILIATION REPORT ===")
        print(f"Total Failed Verifications: {report['total_failed']}")
        print(f"Already Refunded:          {report['already_refunded']}")
        print(f"Needs Refund:              {report['needs_refund']}")
        print(f"Refunded Now:              {report['refunded_now']}")
        print(f"Errors:                    {report['refund_errors']}")
        print(f"Total Credited Back:      ${report['total_amount_refunded']:.2f}")
        print("==============================\n")
        
        if report['needs_refund'] > 0 and dry_run:
            print("To execute refunds, run with --execute flag.")
            
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Namaskah Financial Reconciliation")
    parser.add_argument("--days", type=int, default=30, help="Days back to scan")
    parser.add_argument("--execute", action="store_true", help="Actually process refunds")
    args = parser.parse_args()
    
    asyncio.run(run_reconciliation(days_back=args.days, dry_run=not args.execute))
