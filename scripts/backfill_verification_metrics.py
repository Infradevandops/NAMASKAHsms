"""
Backfill script for verification metrics.
Populates failure_reason and failure_category for historical records.
"""

import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.models.balance_transaction import BalanceTransaction
from app.models.activity import Activity
from app.core.constants import FailureReason, REASON_TO_CATEGORY

def backfill():
    db = SessionLocal()
    try:
        # Find verifications with status 'failed', 'timeout', or 'cancelled' but no category
        records = db.query(Verification).filter(
            Verification.status.in_(['failed', 'timeout', 'cancelled', 'error']),
            Verification.failure_category.is_(None)
        ).all()
        
        print(f"Found {len(records)} records to backfill.")
        
        count = 0
        for v in records:
            reason = None
            if v.status == 'timeout':
                reason = FailureReason.PROVIDER_TIMEOUT
            elif v.status == 'cancelled':
                reason = FailureReason.CANCELLED_BY_USER
            elif v.status == 'failed':
                reason = FailureReason.SMS_NOT_DELIVERED
            elif v.status == 'error':
                reason = FailureReason.PROVIDER_ERROR
            
            if reason:
                v.failure_reason = reason
                v.failure_category = REASON_TO_CATEGORY.get(reason, "OTHER")
                count += 1
        
        db.commit()
        print(f"Successfully backfilled {count} records.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during backfill: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
