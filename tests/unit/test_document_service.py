

import io
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException, UploadFile
from app.services.document_service import DocumentService
from app.services import document_service

class TestDocumentService:
    @pytest.fixture
def service(self, db_session):

        return DocumentService(db_session)

    @pytest.mark.asyncio
    async def test_validate_file_success(self, service):
        # Mock UploadFile
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "test.jpg"
        mock_file.file = io.BytesIO(b"dummy data")

        # Should not raise
        await service._validate_file(mock_file, "passport")

    @pytest.mark.asyncio
    async def test_validate_file_invalid_type(self, service):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "text/plain"
        mock_file.filename = "test.txt"

with pytest.raises(HTTPException) as exc:
            await service._validate_file(mock_file, "passport")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_file_too_large(self, service):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "large.jpg"
        # 6MB for 5MB limit
        mock_file.file = io.BytesIO(b"0" * (6 * 1024 * 1024))

with pytest.raises(HTTPException) as exc:
            await service._validate_file(mock_file, "passport")
        assert exc.value.status_code == 400

def test_generate_file_hash(self, service):

        content = b"hello world"
        h = service._generate_file_hash(content)
        assert len(h) == 64  # SHA-256

    @pytest.mark.asyncio
    async def test_upload_document_profile_not_found(self, service):
        mock_file = MagicMock(spec=UploadFile)
        # Service suppresses HTTPException and returns None (based on pass block)
        assert await service.upload_document(mock_file, "passport", "non-existent-id") is None

    @pytest.mark.asyncio
    async def test_process_image_no_pil(self, service):
        # Even if PIL is available, we can mock it as missing if we want,
        # but let's test what happens when it's called

        document_service.PIL_AVAILABLE = False

        res = await service._process_image("path/to/img.jpg", "passport")
        assert res["error"] == "Image processing unavailable"

        document_service.PIL_AVAILABLE = True  # reset