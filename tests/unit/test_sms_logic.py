

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from app.models.verification import Verification
from app.services.smart_routing import SmartRouter
from app.services.sms_gateway import SMSGateway

class TestSMSLogic:
    @pytest.fixture
    def smart_router(self):

        return SmartRouter()

        @pytest.fixture
    def sms_gateway(self):

        return SMSGateway()

    async def test_smart_router_select_provider_default(self, smart_router, db_session):
        # With no data, it should still return a provider (highest score based on defaults)
        provider = await smart_router.select_provider("telegram", "US")
        assert provider in ["5sim", "sms_activate", "getsms", "textverified"]

    async def test_smart_router_logic_with_stats(self, smart_router, db_session):
        # 1. Seed data to make one provider look better
        # Provider A: High success, Low cost
        # Provider B: Low success, High cost

        # Provider: 5sim
        db_session.add(
            Verification(
                user_id="test_user",
                service_name="telegram",
                provider="5sim",
                status="completed",
                cost=0.5,
                created_at=datetime.now(timezone.utc),
            )
        )

        # Provider: sms_activate (Failing one)
        db_session.add(
            Verification(
                user_id="test_user",
                service_name="telegram",
                provider="sms_activate",
                status="failed",
                cost=2.0,
                created_at=datetime.now(timezone.utc),
            )
        )

        db_session.commit()

        # 2. Select provider
        provider = await smart_router.select_provider("telegram", "US")

        # 5sim should have higher score due to lower cost (1/0.5=2) and higher success rate (1.0 vs 0.0)
        assert provider == "5sim"

    def test_calculate_score(self, smart_router):

        stats_good = {"success_rate": 0.9, "avg_cost": 0.5, "reliability": 0.9}
        stats_bad = {"success_rate": 0.2, "avg_cost": 2.0, "reliability": 0.2}

        score_good = smart_router._calculate_score(stats_good)
        score_bad = smart_router._calculate_score(stats_bad)

        assert score_good > score_bad

        @patch("httpx.AsyncClient.post")
    async def test_sms_gateway_provider_switch(self, mock_post, sms_gateway):
        # Test twilio (default)
        res = await sms_gateway.send_sms("+123456789", "Hello")
        assert res["provider"] == "twilio"

        # Switch to webhook
        sms_gateway.provider = "webhook"

        mock_post.return_value = AsyncMock()
        mock_post.return_value.status_code = 200

        res = await sms_gateway.send_sms("+123456789", "Hello")
        assert res["provider"] == "webhook"
