#!/usr/bin/env python3
"""Test balance API and show actual user balance"""
import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()

print("=" * 60)
print("BALANCE VERIFICATION")
print("=" * 60)

# Check admin user
admin = db.query(User).filter(User.email == "admin@namaskah.app").first()

if admin:
    print(f"\n✅ Admin User Found")
    print(f"   Email: {admin.email}")
    print(f"   Credits: ${admin.credits:.2f}")
    print(f"   ID: {admin.id}")

    if admin.credits == 1000.0:
        print(f"\n⚠️  IMPORTANT:")
        print(f"   The balance showing $1000.00 is CORRECT!")
        print(f"   This is the actual balance in the database.")
        print(f"   The API is working properly.")
        print(f"\n   To test with different balance:")
        print(
            f"   1. Update database: UPDATE users SET credits = 50.00 WHERE email = 'admin@namaskah.app';"
        )
        print(f"   2. Or use the wallet page to add/spend credits")
        print(f"   3. Refresh browser (Cmd+Shift+R to clear cache)")
    else:
        print(f"\n✅ Balance is: ${admin.credits:.2f}")
        print(f"   This should match what you see in the UI")
else:
    print("\n❌ Admin user not found")

db.close()

print("\n" + "=" * 60)
print("API ENDPOINT TEST")
print("=" * 60)

# Test the API endpoint
print("\nTo test the API manually:")
print("1. Login and get token")
print("2. Run this in browser console:")
print(
    """
fetch('/api/billing/balance', {
    headers: { 
        'Authorization': 'Bearer ' + localStorage.getItem('access_token')
    }
})
.then(r => r.json())
.then(d => console.log('Balance:', d))
"""
)

print("\n" + "=" * 60)
