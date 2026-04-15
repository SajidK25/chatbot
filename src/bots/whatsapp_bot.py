import hashlib
import hmac
import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.services.chat_handler import chat_handler

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class WhatsAppMessage(BaseModel):
    from_number: str
    message_body: str
    message_id: str


@router.get("/webhook")
async def verify_webhook(mode: str = "", token: str = "", challenge: str = ""):
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("Webhook verified successfully!")
        return challenge
    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(request: Request):
    if settings.whatsapp_app_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        body = await request.body()

        if not verify_signature(settings.whatsapp_app_secret, body, signature):
            logger.warning("Invalid webhook signature!")
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    logger.info(f"Received webhook: {payload}")

    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        message = messages[0]
        from_number = message.get("from")

        message_type = message.get("type")

        if message_type == "text":
            message_body = message.get("text", {}).get("body", "")
        elif message_type == "interactive":
            button_response = message.get("interactive", {}).get("button_reply", {})
            message_body = button_response.get("id", "")
        else:
            message_body = ""

        logger.info(f"Received message from {from_number}: {message_body}")

        response = await chat_handler.handle_message(message_body, platform="whatsapp")

        await send_whatsapp_message(from_number, response)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")

    return {"status": "ok"}


async def send_whatsapp_message(to: str, message: str):
    import httpx

    url = (
        f"https://graph.facebook.com/v18.0/{settings.whatsapp_phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"Sent WhatsApp message: {response.status_code}")
        return response.json()
