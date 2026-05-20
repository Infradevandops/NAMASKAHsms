import pytest

from app.services.compliance_service import ComplianceService


class TestComplianceService:
    @pytest.fixture
    def service(self, db):
        return ComplianceService(db)

    @pytest.mark.asyncio
    async def test_assess_compliance(self, service):
        result = await service.assess_compliance()
        assert "compliance_score" in result
        assert result["compliance_score"] >= 0.0
        assert result["compliance_score"] <= 100.0
        assert "status" in result

    @pytest.mark.asyncio
    async def test_generate_audit_report(self, service):
        report = await service.generate_audit_report()
        assert "compliance_framework" in report
        assert "SOC 2 Type II" in report["compliance_framework"]
        assert "controls_summary" in report
        # Check that controls_summary has some data
        assert isinstance(report["controls_summary"], dict)
