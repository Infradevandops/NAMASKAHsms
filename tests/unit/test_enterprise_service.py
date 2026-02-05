

from unittest.mock import patch
import pytest
from app.models.enterprise import EnterpriseAccount, EnterpriseTier
from app.services.enterprise_service import EnterpriseService

class TestEnterpriseService:
    @pytest.fixture
    def service(self):

        return EnterpriseService()

        @pytest.mark.asyncio
    async def test_get_user_tier(self, service, db_session, regular_user):
        # Create mocked DB session flow or inject it
        # The service uses get_db() generator directly

        # Setup data
        tier = EnterpriseTier(name="Gold", min_monthly_spend=100.0)
        db_session.add(tier)
        db_session.flush()

        acct = EnterpriseAccount(user_id=regular_user.id, tier_id=tier.id)
        db_session.add(acct)
        db_session.commit()

        # Patch get_db to return our session
        with patch("app.services.enterprise_service.get_db", return_value=iter([db_session])):
            res = await service.get_user_tier(regular_user.id)
            assert res is not None
            assert res["tier_name"] == "Gold"

        @pytest.mark.asyncio
    async def test_get_user_tier_none(self, service, db_session):
        with patch("app.services.enterprise_service.get_db", return_value=iter([db_session])):
            res = await service.get_user_tier("non-existant")
            assert res is None

        @pytest.mark.asyncio
    async def test_upgrade_to_enterprise(self, service, db_session, regular_user):
        tier = EnterpriseTier(name="Platinum", min_monthly_spend=500.0)
        db_session.add(tier)
        db_session.commit()

        with patch("app.services.enterprise_service.get_db", return_value=iter([db_session])):
            res = await service.upgrade_to_enterprise(regular_user.id, "Platinum")
            assert res["success"] is True

            # Verify update
            acct = db_session.query(EnterpriseAccount).filter(EnterpriseAccount.user_id == regular_user.id).first()
            assert acct.tier_id == tier.id

        @pytest.mark.asyncio
    async def test_upgrade_invalid_tier(self, service, db_session, regular_user):
        with patch("app.services.enterprise_service.get_db", return_value=iter([db_session])):
        with pytest.raises(ValueError):
                await service.upgrade_to_enterprise(regular_user.id, "InvalidTier")

        @pytest.mark.asyncio
    async def test_check_sla_compliance(self, service, db_session):
        tier = EnterpriseTier(name="Silver", max_response_time=500, min_monthly_spend=50.0)
        db_session.add(tier)
        db_session.commit()

        # side_effect to return a new iterator each time
        with patch(
            "app.services.enterprise_service.get_db",
            side_effect=lambda: iter([db_session]),
        ):
            # Compliant
            res = await service.check_sla_compliance(200, "Silver")
            assert res["compliant"] is True

            # Violation
            res = await service.check_sla_compliance(600, "Silver")
            assert res["compliant"] is False

        @pytest.mark.asyncio
    async def test_check_sla_invalid_tier(self, service, db_session):
        with patch(
            "app.services.enterprise_service.get_db",
            side_effect=lambda: iter([db_session]),
        ):
            res = await service.check_sla_compliance(100, "Unknown")
            assert res["compliant"] is True  # Default behavior
