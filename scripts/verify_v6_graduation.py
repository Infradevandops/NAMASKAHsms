"""V6.0.0 Graduation Verification Script."""

import sys
import os
import asyncio
import unittest
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.append(os.getcwd())

# Force SQLite fallback for local verification
os.environ["ALLOW_SQLITE_FALLBACK"] = "true"

from app.core.database import SessionLocal
from app.services.pricing_calculator import PricingCalculator
from app.services.rental_service import RentalService
from app.services.analytics_service import AnalyticsService

class V6GraduationTest(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_pricing_rental(self):
        """Test rental pricing logic (Graduation Milestone)."""
        # We calculate for 24 hours at $0.25/hr
        cost_info = PricingCalculator.calculate_rental_cost(self.db, "system_audit", 24.0)
        self.assertEqual(cost_info["total_cost"], 6.00)
        self.assertEqual(cost_info["hourly_rate"], 0.25)

    def test_analytics_readiness_for_v2(self):
        """Test if AnalyticsService is ready for high-density V2 dashboard."""
        async def run_audit():
            analytics = AnalyticsService(self.db)
            overview = await analytics.get_overview()
            # Verify core metric keys exist for the V2 UI
            self.assertIn("revenue", overview)
            self.assertIn("verifications", overview)
            self.assertIn("users", overview)
        
        asyncio.run(run_audit())

    def test_rental_service_instantiation(self):
        """Verify RentalService can be instantiated with its dependencies."""
        service = RentalService(self.db)
        self.assertIsNotNone(service.provider_router)

if __name__ == "__main__":
    print("🚀 Starting V6.0.0 Graduation Verification...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("\n✅ Verification Complete.")
