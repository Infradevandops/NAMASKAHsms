"""User-facing dispute endpoints."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.dispute import (
    Dispute,
    DisputeAttachment,
    DisputeComment,
    DisputeTimeline,
)
from app.services.dispute_service import DisputeService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/disputes", tags=["Disputes"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".gif"}


class OpenDisputeRequest(BaseModel):
    payment_id: str
    reason_code: str
    reason_description: str
    amount: float


class CommentRequest(BaseModel):
    content: str


class ResolveDisputeRequest(BaseModel):
    resolution: str  # approved, rejected
    notes: str


@router.post("/open")
async def open_dispute(
    payload: OpenDisputeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Open a payment dispute."""
    try:
        service = DisputeService(db)
        result = await service.open_dispute(
            user_id=user_id,
            payment_id=payload.payment_id,
            reason_code=payload.reason_code,
            reason_description=payload.reason_description,
            amount=payload.amount,
        )

        # Create timeline event
        timeline = DisputeTimeline(
            dispute_id=result["dispute_id"],
            event_type="opened",
            event_description=f"Dispute opened: {payload.reason_code}",
            actor_id=user_id,
            is_admin=False,
            event_metadata=None,
        )
        db.add(timeline)
        db.commit()

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error opening dispute for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to open dispute")


@router.get("/my")
async def get_my_disputes(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current user's disputes."""
    try:
        disputes = (
            db.query(Dispute)
            .filter(Dispute.user_id == user_id)
            .order_by(Dispute.created_at.desc())
            .all()
        )

        return {
            "disputes": [
                {
                    "id": d.id,
                    "payment_id": d.payment_log_id,
                    "amount": d.amount,
                    "reason_code": d.reason_code,
                    "reason_description": d.reason_description,
                    "status": d.status,
                    "resolution": d.resolution,
                    "created_at": d.created_at.isoformat(),
                    "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                }
                for d in disputes
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching disputes for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch disputes")


@router.get("/{dispute_id}/timeline")
async def get_dispute_timeline(
    dispute_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get timeline for a dispute."""
    try:
        # Verify user owns dispute
        dispute = (
            db.query(Dispute)
            .filter(Dispute.id == dispute_id, Dispute.user_id == user_id)
            .first()
        )

        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        timeline = (
            db.query(DisputeTimeline)
            .filter(DisputeTimeline.dispute_id == dispute_id)
            .order_by(DisputeTimeline.created_at.asc())
            .all()
        )

        return {
            "timeline": [
                {
                    "id": t.id,
                    "event_type": t.event_type,
                    "event_description": t.event_description,
                    "is_admin": t.is_admin,
                    "created_at": t.created_at.isoformat(),
                    "metadata": (
                        json.loads(t.event_metadata) if t.event_metadata else None
                    ),
                }
                for t in timeline
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching timeline for dispute {dispute_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch timeline")


@router.get("/{dispute_id}/comments")
async def get_dispute_comments(
    dispute_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get comments for a dispute."""
    try:
        # Verify user owns dispute
        dispute = (
            db.query(Dispute)
            .filter(Dispute.id == dispute_id, Dispute.user_id == user_id)
            .first()
        )

        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        comments = (
            db.query(DisputeComment)
            .filter(DisputeComment.dispute_id == dispute_id)
            .order_by(DisputeComment.created_at.asc())
            .all()
        )

        return {
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "is_admin": c.is_admin,
                    "created_at": c.created_at.isoformat(),
                }
                for c in comments
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching comments for dispute {dispute_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch comments")


@router.post("/{dispute_id}/comments")
async def add_dispute_comment(
    dispute_id: str,
    payload: CommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add comment to dispute."""
    try:
        # Verify user owns dispute
        dispute = (
            db.query(Dispute)
            .filter(Dispute.id == dispute_id, Dispute.user_id == user_id)
            .first()
        )

        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        # Create comment
        comment = DisputeComment(
            dispute_id=dispute_id,
            user_id=user_id,
            content=payload.content,
            is_admin=False,
        )
        db.add(comment)

        # Add timeline event
        timeline = DisputeTimeline(
            dispute_id=dispute_id,
            event_type="comment_added",
            event_description="User added a comment",
            actor_id=user_id,
            is_admin=False,
            event_metadata=None,
        )
        db.add(timeline)

        db.commit()
        db.refresh(comment)

        return {
            "status": "created",
            "comment_id": comment.id,
            "created_at": comment.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error adding comment to dispute {dispute_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.get("/{dispute_id}/attachments")
async def get_dispute_attachments(
    dispute_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get attachments for a dispute."""
    try:
        # Verify user owns dispute
        dispute = (
            db.query(Dispute)
            .filter(Dispute.id == dispute_id, Dispute.user_id == user_id)
            .first()
        )

        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        attachments = (
            db.query(DisputeAttachment)
            .filter(DisputeAttachment.dispute_id == dispute_id)
            .order_by(DisputeAttachment.uploaded_at.desc())
            .all()
        )

        return {
            "attachments": [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "file_size": a.file_size,
                    "content_type": a.content_type,
                    "url": f"/api/disputes/{dispute_id}/attachments/{a.id}/download",
                    "uploaded_at": a.uploaded_at.isoformat(),
                }
                for a in attachments
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching attachments for dispute {dispute_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch attachments")


@router.post("/{dispute_id}/attachments")
async def upload_dispute_attachment(
    dispute_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload attachment to dispute."""
    try:
        # Verify user owns dispute
        dispute = (
            db.query(Dispute)
            .filter(Dispute.id == dispute_id, Dispute.user_id == user_id)
            .first()
        )

        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB",
            )

        # Save file (in production, upload to S3)
        upload_dir = "uploads/disputes"
        os.makedirs(upload_dir, exist_ok=True)

        safe_filename = (
            f"{dispute_id}_{datetime.now(timezone.utc).timestamp()}_{file.filename}"
        )
        file_path = os.path.join(upload_dir, safe_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # Create attachment record
        attachment = DisputeAttachment(
            dispute_id=dispute_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
        )
        db.add(attachment)

        # Add timeline event
        timeline = DisputeTimeline(
            dispute_id=dispute_id,
            event_type="evidence_uploaded",
            event_description=f"Evidence uploaded: {file.filename}",
            actor_id=user_id,
            is_admin=False,
            event_metadata=json.dumps({"filename": file.filename, "size": file_size}),
        )
        db.add(timeline)

        db.commit()
        db.refresh(attachment)

        logger.info(
            f"Attachment uploaded for dispute {dispute_id}: {file.filename} ({file_size} bytes)"
        )

        return {
            "status": "uploaded",
            "attachment_id": attachment.id,
            "filename": file.filename,
            "file_size": file_size,
            "uploaded_at": attachment.uploaded_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error uploading attachment to dispute {dispute_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to upload attachment")


@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    payload: ResolveDisputeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Resolve a dispute (admin only in production, user can close for now)."""
    try:
        # Verify user owns dispute
        dispute = (
            db.query(Dispute)
            .filter(Dispute.id == dispute_id, Dispute.user_id == user_id)
            .first()
        )

        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        if dispute.status in ["won", "lost", "closed"]:
            raise HTTPException(status_code=400, detail="Dispute already resolved")

        # Update dispute
        dispute.resolution = payload.resolution
        dispute.resolution_notes = payload.notes
        dispute.resolution_date = datetime.now(timezone.utc)
        dispute.status = "closed" if payload.resolution == "rejected" else "won"

        # Add timeline event
        timeline = DisputeTimeline(
            dispute_id=dispute_id,
            event_type="resolved",
            event_description=f"Dispute resolved: {payload.resolution}",
            actor_id=user_id,
            is_admin=False,
            event_metadata=json.dumps(
                {"resolution": payload.resolution, "notes": payload.notes}
            ),
        )
        db.add(timeline)

        db.commit()

        logger.info(f"Dispute {dispute_id} resolved: {payload.resolution}")

        return {
            "status": "resolved",
            "dispute_id": dispute_id,
            "resolution": payload.resolution,
            "resolved_at": dispute.resolution_date.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving dispute {dispute_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve dispute")
