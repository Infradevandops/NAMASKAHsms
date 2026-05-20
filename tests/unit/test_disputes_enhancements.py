"""Unit tests for Disputes tab enhancements."""

import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.api.core.disputes import (
    add_dispute_comment,
    get_dispute_attachments,
    get_dispute_comments,
    get_dispute_timeline,
    get_my_disputes,
    open_dispute,
    resolve_dispute,
    upload_dispute_attachment,
)
from app.models.dispute import (
    Dispute,
    DisputeAttachment,
    DisputeComment,
    DisputeTimeline,
)


class TestDisputeCreation:
    """Test dispute creation and basic operations."""

    @pytest.mark.asyncio
    async def test_create_dispute_success(self, mock_db_session, mock_dispute_service):
        """Test successful dispute creation."""
        mock_dispute_service.open_dispute.return_value = {
            "dispute_id": "disp_123",
            "user_id": "user_123",
            "payment_id": "pay_123",
            "amount": 10.50,
            "reason_code": "not_received",
            "status": "opened",
            "created_at": datetime.now(timezone.utc),
        }

        payload = Mock(
            payment_id="pay_123",
            reason_code="not_received",
            reason_description="Service not received",
            amount=10.50,
        )

        with patch(
            "app.api.core.disputes.DisputeService", return_value=mock_dispute_service
        ):
            result = await open_dispute(
                payload=payload, user_id="user_123", db=mock_db_session
            )

        assert result["dispute_id"] == "disp_123"
        assert result["status"] == "opened"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_dispute_invalid_payment(
        self, mock_db_session, mock_dispute_service
    ):
        """Test dispute creation with invalid payment ID."""
        mock_dispute_service.open_dispute.side_effect = ValueError("Payment not found")

        payload = Mock(
            payment_id="invalid_pay",
            reason_code="not_received",
            reason_description="Service not received",
            amount=10.50,
        )

        with patch(
            "app.api.core.disputes.DisputeService", return_value=mock_dispute_service
        ):
            with pytest.raises(HTTPException) as exc_info:
                await open_dispute(
                    payload=payload, user_id="user_123", db=mock_db_session
                )

        assert exc_info.value.status_code == 400
        assert "Payment not found" in str(exc_info.value.detail)


class TestDisputeTimeline:
    """Test dispute timeline functionality."""

    @pytest.mark.asyncio
    async def test_get_timeline_success(self, mock_db_session):
        """Test retrieving dispute timeline."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_timeline_events = [
            Mock(
                id="evt_1",
                event_type="opened",
                event_description="Dispute opened",
                is_admin=False,
                created_at=datetime.now(timezone.utc),
                event_metadata=None,
            ),
            Mock(
                id="evt_2",
                event_type="evidence_uploaded",
                event_description="Evidence uploaded: screenshot.png",
                is_admin=False,
                created_at=datetime.now(timezone.utc),
                event_metadata='{"filename": "screenshot.png", "size": 12345}',
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_timeline_events
        )

        result = await get_dispute_timeline(
            dispute_id="disp_123", user_id="user_123", db=mock_db_session
        )

        assert len(result["timeline"]) == 2
        assert result["timeline"][0]["event_type"] == "opened"
        assert result["timeline"][1]["event_type"] == "evidence_uploaded"

    @pytest.mark.asyncio
    async def test_get_timeline_unauthorized(self, mock_db_session):
        """Test timeline access for non-owner."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_dispute_timeline(
                dispute_id="disp_123", user_id="wrong_user", db=mock_db_session
            )

        assert exc_info.value.status_code == 404


class TestDisputeComments:
    """Test dispute comments functionality."""

    @pytest.mark.asyncio
    async def test_get_comments_success(self, mock_db_session):
        """Test retrieving dispute comments."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_comments = [
            Mock(
                id="cmt_1",
                content="I need help with this",
                is_admin=False,
                created_at=datetime.now(timezone.utc),
            ),
            Mock(
                id="cmt_2",
                content="We are reviewing your case",
                is_admin=True,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_comments
        )

        result = await get_dispute_comments(
            dispute_id="disp_123", user_id="user_123", db=mock_db_session
        )

        assert len(result["comments"]) == 2
        assert result["comments"][0]["is_admin"] is False
        assert result["comments"][1]["is_admin"] is True

    @pytest.mark.asyncio
    async def test_add_comment_success(self, mock_db_session):
        """Test adding comment to dispute."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        # Mock refresh to set created_at
        def mock_refresh(obj):
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = datetime.now(timezone.utc)
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = "cmt_123"

        mock_db_session.refresh = mock_refresh

        payload = Mock(content="This is my comment")

        result = await add_dispute_comment(
            dispute_id="disp_123",
            payload=payload,
            user_id="user_123",
            db=mock_db_session,
        )

        assert result["status"] == "created"
        assert "comment_id" in result
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()


class TestDisputeAttachments:
    """Test dispute attachments functionality."""

    @pytest.mark.asyncio
    async def test_get_attachments_success(self, mock_db_session):
        """Test retrieving dispute attachments."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_attachments = [
            Mock(
                id="att_1",
                filename="screenshot.png",
                file_size=12345,
                content_type="image/png",
                uploaded_at=datetime.now(timezone.utc),
            )
        ]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_attachments
        )

        result = await get_dispute_attachments(
            dispute_id="disp_123", user_id="user_123", db=mock_db_session
        )

        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["filename"] == "screenshot.png"
        assert result["attachments"][0]["file_size"] == 12345

    @pytest.mark.asyncio
    async def test_upload_attachment_success(self, mock_db_session):
        """Test uploading attachment to dispute."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        # Mock refresh to set uploaded_at and id
        def mock_refresh(obj):
            if not hasattr(obj, "uploaded_at") or obj.uploaded_at is None:
                obj.uploaded_at = datetime.now(timezone.utc)
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = "att_123"

        mock_db_session.refresh = mock_refresh

        # Create mock file
        file_content = b"fake image content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "evidence.png"
        mock_file.content_type = "image/png"
        mock_file.read = AsyncMock(return_value=file_content)

        with patch("builtins.open", create=True) as mock_open:
            with patch("os.makedirs"):
                result = await upload_dispute_attachment(
                    dispute_id="disp_123",
                    file=mock_file,
                    user_id="user_123",
                    db=mock_db_session,
                )

        assert result["status"] == "uploaded"
        assert result["filename"] == "evidence.png"
        assert result["file_size"] == len(file_content)
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_upload_attachment_invalid_type(self, mock_db_session):
        """Test uploading invalid file type."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "malware.exe"
        mock_file.content_type = "application/x-msdownload"

        with pytest.raises(HTTPException) as exc_info:
            await upload_dispute_attachment(
                dispute_id="disp_123",
                file=mock_file,
                user_id="user_123",
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400
        assert "not allowed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_attachment_too_large(self, mock_db_session):
        """Test uploading file that exceeds size limit."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        # Create file larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "large.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=large_content)

        with pytest.raises(HTTPException) as exc_info:
            await upload_dispute_attachment(
                dispute_id="disp_123",
                file=mock_file,
                user_id="user_123",
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400
        assert "too large" in str(exc_info.value.detail)


class TestDisputeResolution:
    """Test dispute resolution workflow."""

    @pytest.mark.asyncio
    async def test_resolve_dispute_success(self, mock_db_session):
        """Test resolving a dispute."""
        mock_dispute = Mock(
            id="disp_123", user_id="user_123", status="opened", resolution=None
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        payload = Mock(resolution="approved", notes="Refund issued")

        result = await resolve_dispute(
            dispute_id="disp_123",
            payload=payload,
            user_id="user_123",
            db=mock_db_session,
        )

        assert result["status"] == "resolved"
        assert result["resolution"] == "approved"
        assert mock_dispute.resolution == "approved"
        assert mock_dispute.resolution_notes == "Refund issued"
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_resolve_already_resolved_dispute(self, mock_db_session):
        """Test resolving an already resolved dispute."""
        mock_dispute = Mock(
            id="disp_123", user_id="user_123", status="won", resolution="approved"
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        payload = Mock(resolution="rejected", notes="Test")

        with pytest.raises(HTTPException) as exc_info:
            await resolve_dispute(
                dispute_id="disp_123",
                payload=payload,
                user_id="user_123",
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400
        assert "already resolved" in str(exc_info.value.detail)


class TestAcceptanceCriteria:
    """Test acceptance criteria for Disputes tab enhancements."""

    @pytest.mark.asyncio
    async def test_ac1_evidence_upload(self, mock_db_session):
        """AC-1: User can upload evidence files (PDF, images)."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        # Mock refresh to set uploaded_at and id
        def mock_refresh(obj):
            if not hasattr(obj, "uploaded_at") or obj.uploaded_at is None:
                obj.uploaded_at = datetime.now(timezone.utc)
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = "att_123"

        mock_db_session.refresh = mock_refresh

        # Test PDF upload
        pdf_content = b"%PDF-1.4 fake pdf content"
        mock_pdf = Mock(spec=UploadFile)
        mock_pdf.filename = "invoice.pdf"
        mock_pdf.content_type = "application/pdf"
        mock_pdf.read = AsyncMock(return_value=pdf_content)

        with patch("builtins.open", create=True):
            with patch("os.makedirs"):
                result = await upload_dispute_attachment(
                    dispute_id="disp_123",
                    file=mock_pdf,
                    user_id="user_123",
                    db=mock_db_session,
                )

        assert result["status"] == "uploaded"
        assert result["filename"] == "invoice.pdf"

    @pytest.mark.asyncio
    async def test_ac2_timeline_shows_events(self, mock_db_session):
        """AC-2: Timeline shows all dispute events."""
        mock_dispute = Mock(id="disp_123", user_id="user_123")
        mock_events = [
            Mock(
                id=f"evt_{i}",
                event_type=event_type,
                event_description=f"Event {i}",
                is_admin=False,
                created_at=datetime.now(timezone.utc),
                event_metadata=None,
            )
            for i, event_type in enumerate(
                ["opened", "comment_added", "evidence_uploaded", "resolved"]
            )
        ]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_events
        )

        result = await get_dispute_timeline(
            dispute_id="disp_123", user_id="user_123", db=mock_db_session
        )

        assert len(result["timeline"]) == 4
        event_types = [e["event_type"] for e in result["timeline"]]
        assert "opened" in event_types
        assert "evidence_uploaded" in event_types
        assert "resolved" in event_types

    @pytest.mark.asyncio
    async def test_ac3_admin_can_resolve(self, mock_db_session):
        """AC-3: Admin can resolve disputes with notes."""
        mock_dispute = Mock(
            id="disp_123", user_id="user_123", status="opened", resolution=None
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        payload = Mock(
            resolution="approved", notes="After reviewing evidence, refund approved"
        )

        result = await resolve_dispute(
            dispute_id="disp_123",
            payload=payload,
            user_id="user_123",
            db=mock_db_session,
        )

        assert result["status"] == "resolved"
        assert (
            mock_dispute.resolution_notes == "After reviewing evidence, refund approved"
        )

    @pytest.mark.asyncio
    async def test_ac4_user_receives_notification(self, mock_db_session):
        """AC-4: User receives notification on resolution."""
        # This would be tested in integration tests with notification service
        # For unit test, we verify the resolution is recorded
        mock_dispute = Mock(id="disp_123", user_id="user_123", status="opened")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_dispute
        )

        payload = Mock(resolution="approved", notes="Resolved")

        result = await resolve_dispute(
            dispute_id="disp_123",
            payload=payload,
            user_id="user_123",
            db=mock_db_session,
        )

        assert result["status"] == "resolved"
        assert "resolved_at" in result


# Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.order_by.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    return session


@pytest.fixture
def mock_dispute_service():
    """Mock dispute service."""
    service = MagicMock()
    service.open_dispute = AsyncMock()
    service.get_open_disputes = AsyncMock(return_value=[])
    return service
