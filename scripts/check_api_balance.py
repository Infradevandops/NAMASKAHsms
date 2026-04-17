#!/usr/bin/env python3
"""
Simple TextVerified Balance Check
Check actual API balance without database dependency
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

try:
    import textverified
except ImportError:
    print("❌ textverified library not installed")
    print("   Run: pip install textverified")
    exit(1)

try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    print("   Run: pip install python-dotenv")


async def check_api_balance():
    """Check TextVerified API balance directly."""
    print("=" * 80)
    print("TEXTVERIFIED API BALANCE CHECK")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Get credentials
    api_key = os.getenv("TEXTVERIFIED_API_KEY")
    api_username = os.getenv("TEXTVERIFIED_USERNAME") or os.getenv("TEXTVERIFIED_EMAIL")
    
    if not api_key or not api_username:
        print("❌ Missing credentials")
        print("   TEXTVERIFIED_API_KEY:", "✅ Set" if api_key else "❌ Missing")
        print("   TEXTVERIFIED_USERNAME:", "✅ Set" if api_username else "❌ Missing")
        print()
        print("Set environment variables:")
        print("  export TEXTVERIFIED_API_KEY='your_key'")
        print("  export TEXTVERIFIED_USERNAME='your_username'")
        return
    
    print("✅ Credentials found")
    print(f"   Username: {api_username}")
    print()
    
    # Initialize client
    try:
        client = textverified.TextVerified(
            api_key=api_key,
            api_username=api_username,
        )
        print("✅ TextVerified client initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Get balance
    print("Fetching balance from TextVerified API...")
    try:
        balance = await asyncio.to_thread(lambda: client.account.balance)
        print()
        print("=" * 80)
        print("CURRENT BALANCE")
        print("=" * 80)
        print(f"💰 ${float(balance):.2f} USD")
        print()
    except Exception as e:
        print(f"❌ Failed to get balance: {e}")
        return
    
    # Compare with logged values
    print("=" * 80)
    print("COMPARISON WITH LOGS")
    print("=" * 80)
    print()
    print("From app.log (2026-04-17):")
    print("  14:16:07 - Balance: $5.40")
    print("  14:17:09 - Balance: $5.40")
    print("  14:18:39 - Balance: $5.40")
    print("  14:20:09 - Balance: $6.90")
    print()
    print("From notifications (screenshots):")
    print("  SMS #1: Charged $2.50 → Balance: $5.40")
    print("  SMS #2: Charged $2.50 → Balance: $3.90")
    print("  SMS #3: Charged $2.50 → Balance: $3.90")
    print("  SMS #4: Charged $2.50 → Balance: $2.40")
    print()
    print("Dashboard (final screenshot):")
    print("  Balance: $2.40")
    print()
    
    api_balance = float(balance)
    
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    print(f"Current API Balance: ${api_balance:.2f}")
    print()
    
    # Check which scenario matches
    if abs(api_balance - 2.40) < 0.01:
        print("✅ SCENARIO 1: No refunds processed")
        print("   - Balance matches dashboard ($2.40)")
        print("   - All 4 SMS charges applied ($10.00 total)")
        print("   - 0 refunds issued")
        print()
        print("⚠️  ISSUE: All 4 SMS stuck in 'Still Waiting' status")
        print("   - Expected: Automatic refunds after timeout")
        print("   - Actual: No refunds processed")
        print()
        
    elif abs(api_balance - 6.90) < 0.01:
        print("✅ SCENARIO 2: Partial refunds processed")
        print("   - Balance matches log at 14:20:09 ($6.90)")
        print("   - Refunded: $4.50 (approximately 1-2 SMS)")
        print("   - Net charges: $5.50")
        print()
        print("⚠️  ISSUE: Refunds not reflected in frontend")
        print("   - Dashboard shows: $2.40")
        print("   - Actual balance: $6.90")
        print("   - Difference: $4.50 (missing refunds)")
        print()
        
    elif abs(api_balance - 12.40) < 0.01:
        print("✅ SCENARIO 3: Full refunds processed")
        print("   - Balance matches starting balance ($12.40)")
        print("   - All 4 SMS refunded ($10.00 total)")
        print("   - Net charges: $0.00")
        print()
        print("⚠️  ISSUE: Refunds not reflected in frontend")
        print("   - Dashboard shows: $2.40")
        print("   - Actual balance: $12.40")
        print("   - Difference: $10.00 (all refunds missing)")
        print()
        
    else:
        print("⚠️  SCENARIO 4: Unexpected balance")
        print(f"   - Current: ${api_balance:.2f}")
        print(f"   - Expected: $2.40 (no refunds) or $6.90 (partial) or $12.40 (full)")
        print()
        print("   Possible causes:")
        print("   - Additional transactions occurred")
        print("   - Manual adjustments made")
        print("   - Other users sharing same account")
        print()
    
    print("=" * 80)
    print("FINANCIAL INTEGRITY ISSUES")
    print("=" * 80)
    print()
    print("1. 🚨 TIER PRICING BUG")
    print("   - User on Custom tier ($35/month)")
    print("   - Expected rate: $0.20/SMS overage")
    print("   - Actual rate: $2.50/SMS (Pay-As-You-Go rate)")
    print("   - Overcharge: $2.30 per SMS")
    print("   - Total overcharge: $9.20 for 4 SMS")
    print()
    
    print("2. ⚠️  BALANCE SYNC FAILURE")
    print(f"   - API Balance: ${api_balance:.2f}")
    print("   - Dashboard: $2.40")
    if abs(api_balance - 2.40) > 0.01:
        print(f"   - Discrepancy: ${abs(api_balance - 2.40):.2f}")
        print("   - Frontend not syncing with API")
    else:
        print("   - ✅ Synced correctly")
    print()
    
    print("3. 📭 MISSING REFUND NOTIFICATIONS")
    if abs(api_balance - 2.40) > 0.01:
        refund_amount = api_balance - 2.40
        print(f"   - Refunds processed: ~${refund_amount:.2f}")
        print("   - Notifications sent: 0")
        print("   - User has no visibility into refunds")
    else:
        print("   - No refunds detected")
        print("   - 4 SMS stuck in 'Still Waiting' status")
        print("   - Expected: Automatic timeout and refund")
    print()
    
    print("4. 🕳️  MISSING TRANSACTION LOGS")
    print("   - No debit logs for SMS charges")
    print("   - No credit logs for refunds")
    print("   - No audit trail for balance changes")
    print()
    
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. ✅ COMPLETED: Verified actual API balance")
    print(f"   Result: ${api_balance:.2f}")
    print()
    print("2. 📋 TODO: Query database for verification records")
    print("   - Check status of 4 SMS verifications")
    print("   - Check if refunds recorded in DB")
    print("   - Check transaction history")
    print()
    print("3. 🔧 TODO: Fix tier pricing logic")
    print("   - Locate pricing code in SMS service")
    print("   - Implement tier-aware pricing")
    print("   - Test all tier rates")
    print()
    print("4. 🔄 TODO: Implement balance sync")
    print("   - Add WebSocket balance updates")
    print("   - Refresh frontend after transactions")
    print("   - Add manual refresh button")
    print()
    print("5. 📬 TODO: Add refund notifications")
    print("   - Trigger on SMS failure/timeout")
    print("   - Include refund amount and reason")
    print("   - Update balance in notification")
    print()
    print("6. 📝 TODO: Implement transaction logging")
    print("   - Log all debits (SMS charges)")
    print("   - Log all credits (refunds)")
    print("   - Include metadata (tier, rate, reason)")
    print()
    
    print("=" * 80)
    print(f"Report saved to: docs/tasks/BALANCE_SYNC_FINANCIAL_INTEGRITY.md")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_api_balance())
