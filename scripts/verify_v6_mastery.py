"""Verification script for V6.0 Institutional Mastery."""

import asyncio
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.system import ActivityLog, ServiceStatus
from app.models.verification import Verification
from app.services.providers.provider_health_check import perform_liquidity_audit
from app.services.verification_status_service import mark_verification_transcribing
from app.services.providers.provider_router import ProviderRouter
from app.core.textverified_health import get_health_monitor

async def verify_mastery():
    print("🚀 Starting V6.0 Institutional Mastery Verification...")
    db = SessionLocal()
    
    try:
        # 1. Verify Liquidity Audit
        print("\n--- 1. Liquidity Audit Verification ---")
        # We manually trigger an audit
        # To ensure we get a "low balance" alert, we can mock one provider balance if needed
        # but for now we'll just check if it runs without errors.
        await perform_liquidity_audit(db)
        
        # Check if any logs were created
        logs = db.query(ActivityLog).filter(ActivityLog.action == "LIQUIDITY_ALARM").all()
        print(f"Detected {len(logs)} liquidity alarms in DB.")
        for log in logs:
            print(f"  [ALARM] Provider: {log.element}, Status: {log.status}, Details: {log.details}")

        # 2. Verify Health-Aware Routing Logic
        print("\n--- 2. Health-Aware Routing Verification ---")
        monitor = get_health_monitor()
        # Mock a degraded state
        monitor.last_status = "degraded"
        monitor.response_times = [6000.0] * 10
        metrics = monitor.get_metrics()
        print(f"Mocked monitor status: {metrics['status']}")
        
        router = ProviderRouter()
        # This should log a warning about degradation and allow candidates to compete
        # Note: If no other US providers are enabled, it might still return TV or fail.
        # We're just checking that it doesn't return TV *immediately* as it used to.
        print("Calling get_provider for US...")
        provider, city_honoured, note = await router.get_provider(
            db, service="google", country="US", capability="sms"
        )
        print(f"Router selected: {provider.name if provider else 'None'}")

        # 3. Verify Transcribing State logic
        print("\n--- 3. Voice Transcribing State Verification ---")
        # Create a mock verification
        mock_v = Verification(
            user_id="SYSTEM_TEST",
            service_name="voice_test",
            phone_number="+15550199",
            status="pending",
            capability="voice",
            provider="textverified",
            cost=2.50
        )
        db.add(mock_v)
        db.commit()
        
        print(f"Initial status: {mock_v.status}")
        await mark_verification_transcribing(db, mock_v, audio_url="https://audio.mock/123.mp3")
        
        # Reload
        db.refresh(mock_v)
        print(f"Status after marking: {mock_v.status}")
        print(f"Audio URL: {mock_v.audio_url}")
        
        if mock_v.status == "transcribing" and mock_v.audio_url:
            print("✅ Transcribing state logic verified.")
        else:
            print("❌ Transcribing state logic failed.")

        # Cleanup mock
        db.delete(mock_v)
        db.commit()

    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n--- Verification Complete ---")

if __name__ == "__main__":
    # Ensure background tasks don't block and use local SQLite
    os.environ["ALLOW_SQLITE_FALLBACK"] = "true"
    os.environ["USE_TEST_DB"] = "true"
    asyncio.run(verify_mastery())
