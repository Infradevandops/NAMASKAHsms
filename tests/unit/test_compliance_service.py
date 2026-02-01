

import pytest
from app.services.compliance_service import ComplianceService

class TestComplianceService:
    @pytest.fixture
def service(self):

        return ComplianceService()

    @pytest.mark.asyncio
    async def test_assess_compliance(self, service):
        result = await service.assess_compliance()
        assert "compliance_score" in result
        assert result["compliance_score"] == 100.0  # All mocked as compliant
        assert result["status"] == "compliant"

    @pytest.mark.asyncio
    async def test_generate_audit_report(self, service):
        report = await service.generate_audit_report()
        assert report["compliance_framework"] == "SOC 2 Type II"
        assert "controls_summary" in report
        assert report["controls_summary"]["total_controls"] == 9