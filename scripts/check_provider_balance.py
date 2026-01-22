#!/usr/bin/env python3
"""Check TextVerified provider balance."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.textverified_service import TextVerifiedService
from app.core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Check balance."""
    print("="*60)
    print("TEXTVERIFIED BALANCE CHECK")
    print("="*60)
    
    try:
        service = TextVerifiedService()
        
        if not service.enabled:
            print("❌ TextVerified service not enabled")
            print("   Check API credentials in environment")
            return 1
        
        print("✅ Service initialized")
        print(f"   API Key: {service.api_key[:10]}..." if service.api_key else "   No API key")
        print(f"   Username: {service.api_username}")
        
        print("\n📊 Fetching balance...")
        balance_data = await service.get_balance()
        
        balance = balance_data.get('balance', 0)
        cached = balance_data.get('cached', False)
        
        print(f"\n💰 Current Balance: ${balance:.2f} USD")
        print(f"   Cached: {'Yes' if cached else 'No'}")
        
        # Estimate remaining verifications
        avg_cost = 0.50  # Average cost per verification
        estimated_verifications = int(balance / avg_cost)
        
        print(f"\n📱 Estimated Verifications: ~{estimated_verifications}")
        print(f"   (Based on ${avg_cost:.2f} avg cost)")
        
        # Warning thresholds
        if balance < 10:
            print("\n⚠️  WARNING: Low balance! Add funds soon.")
        elif balance < 50:
            print("\n⚠️  Balance getting low. Consider adding funds.")
        else:
            print("\n✅ Balance healthy")
        
        print("\n" + "="*60)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Balance check failed: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
