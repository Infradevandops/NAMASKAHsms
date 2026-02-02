

import pytest
from app.models.affiliate import AffiliateApplication
from app.services.affiliate_service import AffiliateService
from app.services.mfa_service import MFAService
import pyotp
import pyotp

class TestAffiliateService:
    @pytest.fixture
    def service(self):

        return AffiliateService()

        @pytest.mark.asyncio
    async def test_create_application(self, service, db_session):
        email = "aff@ex.com"
        res = await service.create_application(email, "individual", ["API"], "Hello", db_session)
        assert res["status"] == "pending"

        # Verify DB
        app = db_session.query(AffiliateApplication).filter(AffiliateApplication.email == email).first()
        assert app is not None
        assert app.program_type == "individual"

        @pytest.mark.asyncio
    async def test_duplicate_application(self, service, db_session):
        email = "dup@ex.com"
        await service.create_application(email, "individual", [], None, db_session)
        with pytest.raises(ValueError, match="already have a pending application"):
            await service.create_application(email, "individual", [], None, db_session)

        @pytest.mark.asyncio
    async def test_update_status(self, service, db_session):
        email = "upd@ex.com"
        app_res = await service.create_application(email, "individual", [], None, db_session)

        res = await service.update_application_status(app_res["id"], "approved", "Good to go", db_session)
        assert res["success"] is True
        assert res["status"] == "approved"

        app = db_session.get(AffiliateApplication, app_res["id"])
        assert app.status == "approved"
        assert app.admin_notes == "Good to go"


class TestMFAService:

    def test_generate_secret(self):

        pass

        secret = MFAService.generate_secret()
        assert len(secret) == 32  # Base32 default

    def test_verify_token(self):

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        token = totp.now()

        assert MFAService.verify_token(secret, token) is True
        assert MFAService.verify_token(secret, "000000") is False

    def test_generate_qr_code(self):

        secret = pyotp.random_base32()
        qr_b64 = MFAService.generate_qr_code("test@ex.com", secret)
        assert isinstance(qr_b64, str)
        assert len(qr_b64) > 100