#!/usr/bin/env python3
"""Update admin balance for testing"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()

print("=" * 60)
print("UPDATE ADMIN BALANCE")
print("=" * 60)

admin = db.query(User).filter(User.email == 'admin@namaskah.app').first()

if admin:
    old_balance = admin.credits
    
    # Set to a different amount to prove it's dynamic
    new_balance = 47.50
    
    admin.credits = new_balance
    db.commit()
    
    print(f"\n✅ Balance Updated!")
    print(f"   Old Balance: ${old_balance:.2f}")
    print(f"   New Balance: ${new_balance:.2f}")
    print(f"\n📋 Next Steps:")
    print(f"   1. Go to browser")
    print(f"   2. Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)")
    print(f"   3. Balance should now show ${new_balance:.2f}")
    print(f"\n   This proves the balance is fetched from API!")
else:
    print("\n❌ Admin user not found")

db.close()
print("\n" + "=" * 60)
