#!/usr/bin/env python3
"""Verify user balances in database."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.balance_transaction import BalanceTransaction

Session = sessionmaker(bind=engine)
db = Session()

print("\n" + "="*70)
print("USER BALANCE VERIFICATION")
print("="*70)

users = db.query(User).all()

for user in users:
    transactions = db.query(BalanceTransaction).filter_by(user_id=user.id).all()
    calculated = sum(t.amount for t in transactions)
    
    status = "✅" if abs(user.credits - calculated) < 0.01 else "❌"
    
    print(f"\n{status} {user.email}")
    print(f"   Database Balance: ${user.credits:.2f}")
    print(f"   Calculated:       ${calculated:.2f}")
    print(f"   Transactions:     {len(transactions)}")
    
    if abs(user.credits - calculated) > 0.01:
        print(f"   ⚠️  MISMATCH: ${abs(user.credits - calculated):.2f}")

print("\n" + "="*70)
print(f"Total Users: {len(users)}")
print("="*70 + "\n")
