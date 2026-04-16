import asyncio
import hashlib
import hmac
import logging
import time
from collections import defaultdict
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.services.chat_handler import chat_handler

logger = logging.getLogger(__name__)
router = APIRouter()


class RateLimiter:
    """In-memory rate limiter: 10 searches per minute per user"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup(user_id, now)
        return len(self._requests[user_id]) < self.max_requests

    def record_search(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup(user_id, now)
        if len(self._requests[user_id]) >= self.max_requests:
            return False
        self._requests[user_id].append(now)
        return True

    def _cleanup(self, user_id: str, now: float):
        cutoff = now - self.window_seconds
        self._requests[user_id] = [t for t in self._requests[user_id] if t > cutoff]


rate_limiter = RateLimiter()


async def with_retry(
    func, *args, max_attempts: int = 3, base_delay: float = 0.5, **kwargs
):
    """Execute function with exponential backoff retry"""
    last_exception = None
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
    raise last_exception


def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class WhatsAppMessage(BaseModel):
    from_number: str
    message_body: str
    message_id: str


def verify_webhook(mode: str = "", token: str = "", challenge: str = ""):
    """Verify webhook - sync version for testing"""
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("Webhook verified successfully!")
        return challenge
    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    raise HTTPException(status_code=403, detail="Verification failed")


async def verify_webhook_async(mode: str = "", token: str = "", challenge: str = ""):
    """Verify webhook - async version for FastAPI"""
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("Webhook verified successfully!")
        return challenge
    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    raise HTTPException(status_code=403, detail="Verification failed")


async def handle_webhook_payload(payload: dict, handler, send_func):
    """Handle webhook payload - extracted for testing"""
    start_time = time.time()

    entry = payload.get("entry", [])
    if not entry:
        return {"status": "ok"}

    changes = entry[0].get("changes", [])
    if not changes:
        return {"status": "ok"}

    value = changes[0].get("value", {})
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

    if not rate_limiter.is_allowed(from_number):
        logger.warning(f"Rate limit exceeded for user {from_number}")
        return {"status": "ok"}

    try:
        response = await with_retry(
            handler.handle_message,
            message_body,
            platform="whatsapp",
            max_attempts=3,
            base_delay=0.5,
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return {"status": "ok"}

    try:
        await with_retry(
            send_func, from_number, response, max_attempts=3, base_delay=0.5
        )
    except Exception as e:
        logger.error(f"Error sending response: {e}", exc_info=True)

    elapsed = time.time() - start_time
    logger.info(f"Response completed in {elapsed:.2f}s")

    return {"status": "ok"}


@router.get("/webhook")
async def verify_webhook_endpoint(mode: str = "", token: str = "", challenge: str = ""):
    return await verify_webhook_async(mode, token, challenge)


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

    return await handle_webhook_payload(payload, chat_handler, send_whatsapp_message)


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
