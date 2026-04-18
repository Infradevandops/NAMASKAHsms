"""
Institutional Financial Integrity Audit Script.
Verifies consistency between User balances, Analytics Transactions, and strict Audit Logs.
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.user import User, Referral, Subscription, Webhook
from app.models.transaction import Transaction, PaymentLog
from app.models.balance_transaction import BalanceTransaction
from app.models.verification import Verification
from app.models.user_preference import UserPreference
from app.models.activity import Activity
from app.models.notification import Notification
from app.models.device_token import DeviceToken
from app.models.enterprise import EnterpriseAccount
from app.models.reseller import ResellerAccount
from app.models.notification_preference import NotificationPreference

def run_audit():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    print("=" * 60)
    print(f"FINANCIAL INTEGRITY AUDIT - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    users = db.query(User).all()
    total_anomalies = 0

    for user in users:
        print(f"\nAuditing User: {user.email} (ID: {user.id})")
        
        # 1. Current Balance
        current_balance = float(user.credits or 0.0)
        
        # 2. Sum of BalanceTransactions (Audit Trail)
        audit_sum = db.query(func.sum(BalanceTransaction.amount)).filter(
            BalanceTransaction.user_id == user.id
        ).scalar() or 0.0
        
        # 3. Sum of Transactions (Analytics)
        analytics_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id
        ).scalar() or 0.0

        # Check for Balance-Audit discrepancy
        # Note: Allow small epsilon for floating point issues
        discrepancy = abs(current_balance - audit_sum)
        if discrepancy > 0.01:
            print(f"  [!] BALANCE ANOMALY DETECTED")
            print(f"      - Current Balance: ${current_balance:.2f}")
            print(f"      - Audit Trail Sum: ${audit_sum:.2f}")
            print(f"      - Discrepancy:     ${discrepancy:.2f}")
            total_anomalies += 1
        else:
            print(f"  [✓] Balance matches Audit Trail (${current_balance:.2f})")

        # Check for Analytics-Audit discrepancy
        analytics_audit_diff = abs(analytics_sum - audit_sum)
        if analytics_audit_diff > 0.01:
            print(f"  [!] LOGGING MISMATCH DETECTED")
            print(f"      - Analytics Sum:   ${analytics_sum:.2f}")
            print(f"      - Audit Trail Sum: ${audit_sum:.2f}")
            print(f"      - Difference:      ${analytics_audit_diff:.2f}")
            print(f"      (Recommendation: Check for legacy untracked transactions)")
        else:
            print(f"  [✓] Analytics matches Audit Trail (${analytics_sum:.2f})")

    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY")
    print("-" * 60)
    print(f"Total Users Audited: {len(users)}")
    print(f"Critical Anomalies:  {total_anomalies}")
    print("=" * 60)
    
    if total_anomalies == 0:
        print("RESULT: PASS - Financial integrity is strictly enforced.")
    else:
        print("RESULT: FAIL - Reconciliation required for anomalous accounts.")

if __name__ == "__main__":
    run_audit()
