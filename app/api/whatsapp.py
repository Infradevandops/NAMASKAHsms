"""WhatsApp Business API endpoints."""
from fastapi import APIRouter, HTTPException, Request

from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
whatsapp_service = WhatsAppService()


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Verify WhatsApp webhook."""
    params = request.query_params
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    result = await whatsapp_service.verify_webhook(token, challenge)
    if result:
        return int(result)
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle WhatsApp webhook events."""
    data = await request.json()
    # Process incoming messages
    return {"status": "ok"}
