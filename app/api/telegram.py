"""Telegram Bot API endpoints."""
from fastapi import APIRouter, Request
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])
telegram_service = TelegramService()

@router.post("/webhook")
async def handle_telegram_webhook(request: Request):
    """Handle Telegram webhook updates."""
    data = await request.json()
    
    # Process incoming messages
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        
        if text.startswith("/start"):
            await telegram_service.send_verification_code(
                str(chat_id), 
                "Welcome to Namaskah SMS verification!"
            )
    
    return {"status": "ok"}