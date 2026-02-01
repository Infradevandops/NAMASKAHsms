

import pytest
from app.services.disaster_recovery import DisasterRecoveryService

class TestDisasterRecoveryService:
    @pytest.fixture
def service(self):

        return DisasterRecoveryService()

    @pytest.mark.asyncio
    async def test_create_backup(self, service):
        backup = await service.create_backup("full")
        assert backup["type"] == "full"
        assert backup["status"] == "completed"
        assert "database" in backup["components"]

    @pytest.mark.asyncio
    async def test_test_recovery(self, service):
        recovery = await service.test_recovery("backup_123")
        assert recovery["backup_id"] == "backup_123"
        assert recovery["status"] == "success"
        assert recovery["rto_met"] is True

    @pytest.mark.asyncio
    async def test_get_recovery_status(self, service):
        status = await service.get_recovery_status()
        assert status["dr_ready"] is True
        assert status["backup_locations"] == 3