#!/usr/bin/env python3
"""
URGENT: Issue Manual Refund
User charged $10.00 for failed SMS verifications due to tier pricing bug
"""

import asyncio
import sys
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, '.')

async def issue_refund():
    """Issue $10.00 refund to affected user."""
    
    print("=" * 80)
    print("🚨 URGENT REFUND PROCEDURE")
    print("=" * 80)
    print()
    
    from app.core.database import get_db
    from app.models.user import User
    from app.models.verification import SMSVerification
    from sqlalchemy import select, update
    
    user_id = "2986207f-4e45-4249-91c3-e5e13bae6622"
    refund_amount = Decimal("10.00")
    
    print(f"User ID: {user_id}")
    print(f"Refund Amount: ${refund_amount:.2f}")
    print(f"Reason: Tier pricing bug + 4 failed SMS verifications")
    print()
    
    async for db in get_db():
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ ERROR: User {user_id} not found")
            return
        
        print("=" * 80)
        print("USER DETAILS")
        print("=" * 80)
        print(f"Email: {user.email}")
        print(f"Tier: {user.subscription_tier}")
        print(f"Current Balance: ${user.balance:.2f}")
        print()
        
        # Get failed SMS verifications
        result = await db.execute(
            select(SMSVerification)
            .where(SMSVerification.user_id == user_id)
            .where(SMSVerification.created_at >= datetime(2026, 4, 17, 14, 0, 0))
            .order_by(SMSVerification.created_at.desc())
        )
        verifications = result.scalars().all()
        
        print("=" * 80)
        print("FAILED SMS VERIFICATIONS")
        print("=" * 80)
        
        if not verifications:
            print("⚠️  No verifications found for this date")
            print()
        else:
            total_cost = Decimal("0.00")
            for i, v in enumerate(verifications, 1):
                print(f"{i}. {v.service} - {v.phone_number}")
                print(f"   Status: {v.status}")
                print(f"   Cost: ${v.cost:.2f}")
                print(f"   Created: {v.created_at}")
                total_cost += Decimal(str(v.cost))
                print()
            
            print(f"Total Cost: ${total_cost:.2f}")
            print()
        
        # Calculate new balance
        old_balance = user.balance
        new_balance = old_balance + refund_amount
        
        print("=" * 80)
        print("REFUND CALCULATION")
        print("=" * 80)
        print(f"Current Balance: ${old_balance:.2f}")
        print(f"Refund Amount: ${refund_amount:.2f}")
        print(f"New Balance: ${new_balance:.2f}")
        print()
        
        print("=" * 80)
        print("CONFIRMATION")
        print("=" * 80)
        print("⚠️  This will:")
        print(f"   1. Add ${refund_amount:.2f} to user balance")
        print(f"   2. Update {len(verifications)} SMS verifications to REFUNDED status")
        print(f"   3. Send notification to user (if available)")
        print()
        
        confirm = input("Proceed with refund? Type 'YES' to confirm: ")
        
        if confirm != 'YES':
            print()
            print("❌ Refund cancelled by user")
            return
        
        print()
        print("Processing refund...")
        print()
        
        # Update user balance
        user.balance = new_balance
        
        # Update SMS verifications
        if verifications:
            for v in verifications:
                v.status = "REFUNDED"
                v.refunded = True
                v.refund_amount = v.cost
                v.refund_reason = "Tier pricing bug - manual refund issued"
                v.updated_at = datetime.utcnow()
        
        # Commit changes
        await db.commit()
        
        print("=" * 80)
        print("✅ REFUND ISSUED SUCCESSFULLY")
        print("=" * 80)
        print(f"Old Balance: ${old_balance:.2f}")
        print(f"New Balance: ${new_balance:.2f}")
        print(f"Refunded: ${refund_amount:.2f}")
        print(f"SMS Updated: {len(verifications)}")
        print()
        
        # Try to send notification
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(db)
            
            await notification_service.create_notification(
                user_id=user.id,
                type="refund",
                title="Refund Processed - $10.00",
                message=f"We've refunded ${refund_amount:.2f} due to a system error that affected your SMS verifications. We sincerely apologize for the inconvenience.",
                category="billing",
                metadata={
                    "amount": float(refund_amount),
                    "reason": "tier_pricing_bug",
                    "sms_count": len(verifications),
                    "old_balance": float(old_balance),
                    "new_balance": float(new_balance)
                }
            )
            
            await db.commit()
            print("✅ Notification sent to user")
            print()
        except Exception as e:
            print(f"⚠️  Could not send notification: {e}")
            print("   (Refund still processed successfully)")
            print()
        
        # Create transaction log if table exists
        try:
            from app.models.transaction import Transaction
            
            transaction = Transaction(
                user_id=user.id,
                transaction_type="REFUND",
                amount=refund_amount,
                description=f"Manual refund: Tier pricing bug + {len(verifications)} failed SMS",
                status="COMPLETED",
                metadata={
                    "reason": "tier_pricing_bug",
                    "sms_count": len(verifications),
                    "old_balance": float(old_balance),
                    "new_balance": float(new_balance),
                    "issued_by": "admin",
                    "issue_date": datetime.utcnow().isoformat()
                }
            )
            
            db.add(transaction)
            await db.commit()
            
            print("✅ Transaction log created")
            print()
        except Exception as e:
            print(f"⚠️  Could not create transaction log: {e}")
            print("   (Refund still processed successfully)")
            print()
        
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("1. ✅ Refund issued")
        print("2. 📧 Send email to user explaining the refund")
        print("3. 🔧 Fix tier pricing bug (see BALANCE_VERIFIED.md)")
        print("4. 🔧 Implement SMS timeout & auto-refund")
        print("5. 🔍 Audit other Custom tier users for similar issues")
        print()
        
        print("Email template saved to: docs/tasks/URGENT_REFUND_PROCEDURE.md")
        print()
        
        break


if __name__ == "__main__":
    try:
        asyncio.run(issue_refund())
    except KeyboardInterrupt:
        print("\n\n❌ Refund cancelled by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        print("\nIf database connection failed, try:")
        print("1. Check DATABASE_URL in .env")
        print("2. Ensure PostgreSQL is running")
        print("3. Use manual SQL method (see URGENT_REFUND_PROCEDURE.md)")
