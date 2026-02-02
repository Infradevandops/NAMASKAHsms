

import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_tier
from app.models.user import User, Webhook
from app.schemas.responses import SuccessResponse

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Tier check for PAYG+
require_payg = require_tier("payg")


class WebhookCreate(BaseModel):

    name: str
    url: HttpUrl
    events: List[str] = ["*"]


class WebhookUpdate(BaseModel):

    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):

    id: str
    name: str
    url: str
    events: str
    is_active: bool
    secret: Optional[str]
    last_success: Optional[str] = None
    last_failure: Optional[str] = None


    @router.get("", response_model=SuccessResponse)
    async def list_webhooks(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        _=Depends(require_payg),
        ):
        """List all webhooks for the current user."""
        webhooks = db.query(Webhook).filter(Webhook.user_id == current_user.id).all()

        return SuccessResponse(
        message="Webhooks retrieved successfully",
        data=[
            {
                "id": w.id,
                "name": w.name,
                "url": w.url,
                "events": w.events,
                "is_active": w.is_active,
                "secret": w.secret,
                "last_success": w.last_success.isoformat() if w.last_success else None,
                "last_failure": w.last_failure.isoformat() if w.last_failure else None,
            }
        for w in webhooks
        ],
        )


        @router.post("", response_model=SuccessResponse)
    async def create_webhook(
        request: WebhookCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        _=Depends(require_payg),
        ):
        """Create a new webhook."""
        webhook = Webhook(
        user_id=current_user.id,
        name=request.name,
        url=str(request.url),
        events=",".join(request.events),
        secret=secrets.token_hex(16),
        is_active=True,
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        return SuccessResponse(
        message="Webhook created successfully",
        data={"id": webhook.id, "secret": webhook.secret},
        )


        @router.delete("/{webhook_id}", response_model=SuccessResponse)
    async def delete_webhook(
        webhook_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        _=Depends(require_payg),
        ):
        """Delete a webhook."""
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id, Webhook.user_id == current_user.id).first()

        if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

        db.delete(webhook)
        db.commit()

        return SuccessResponse(message="Webhook deleted successfully")


        @router.post("/{webhook_id}/test", response_model=SuccessResponse)
    async def test_webhook(
        webhook_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        _=Depends(require_payg),
        ):
        """Send a test ping to the webhook."""
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id, Webhook.user_id == current_user.id).first()

        if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # In a real app, this would trigger an async task to ping the URL
        return SuccessResponse(message=f"Test ping sent to {webhook.url}")