#!/usr/bin/env python3
"""Purchase new 215 number and monitor for SMS."""

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '/Users/machine/Desktop/Namaskah. app')

from app.services.textverified_service import TextVerifiedService

async def purchase_and_monitor():
    tv_service = TextVerifiedService()
    
    # Check balance
    balance = await tv_service.get_balance()
    print(f"💰 Balance: ${balance['balance']:.2f}")
    
    if balance['balance'] < 3.50:
        print("❌ Insufficient balance")
        return
    
    # Purchase new number
    print(f"\n📞 Purchasing NEW 215 Philadelphia number...")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        result = await tv_service.create_verification(
            service="telegram",
            area_code="215"
        )
        
        print(f"\n✅ PURCHASED!")
        print(f"   Phone: {result['phone_number']}")
        print(f"   ID: {result['id']}")
        print(f"   Cost: ${result['cost']:.2f}")
        
        verification_id = result['id']
        phone = result['phone_number']
        
    except Exception as e:
        print(f"❌ Purchase failed: {e}")
        return
    
    # Monitor for SMS
    print(f"\n📨 MONITORING FOR SMS (5 minutes)...")
    print(f"   Use this number on Telegram: {phone}")
    print(f"   Checking every 5 seconds...\n")
    
    max_attempts = 60  # 5 minutes
    
    for attempt in range(1, max_attempts + 1):
        elapsed = attempt * 5
        mins = elapsed // 60
        secs = elapsed % 60
        
        try:
            status = await tv_service.check_sms(verification_id)
            
            if status['status'] == 'received' and status['sms_code']:
                print(f"\n\n🎉 SMS CODE RECEIVED!")
                print(f"=" * 60)
                print(f"   CODE: {status['sms_code']}")
                print(f"   Full Text: {status['sms_text']}")
                print(f"=" * 60)
                return
            
            print(f"   [{mins:02d}:{secs:02d}] Attempt {attempt}/{max_attempts} - Status: {status['status']}", end='\r')
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
    
    print(f"\n\n⏱️  TIMEOUT - No SMS received after 5 minutes")
    print(f"   Verification ID: {verification_id}")
    print(f"   Status: Will auto-timeout and charge $3.20")

if __name__ == "__main__":
    asyncio.run(purchase_and_monitor())
