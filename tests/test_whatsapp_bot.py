import pytest
import time
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from collections import defaultdict


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


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_allow_10_searches_per_minute(self):
        """GIVEN user sends 10 valid messages within 1 minute WHEN each message is processed THEN all 10 are processed"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_id = "+1234567890"

        results = [limiter.record_search(user_id) for _ in range(10)]

        assert all(results), "All 10 searches should be allowed"

    def test_skip_when_rate_limit_exceeded(self):
        """GIVEN user sends 11 messages within 1 minute WHEN the 11th message is processed THEN processing is skipped, no response sent"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_id = "+1234567890"

        for _ in range(10):
            limiter.record_search(user_id)

        result = limiter.record_search(user_id)

        assert result is False, "11th search should be skipped"

    def test_separate_limit_per_user(self):
        """GIVEN user A sends 10 messages, user B sends first message WHEN each message is processed THEN user A is skipped, user B is processed"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_a = "+1234567890"
        user_b = "+0987654321"

        for _ in range(10):
            limiter.record_search(user_a)

        result_a = limiter.is_allowed(user_a)
        result_b = limiter.is_allowed(user_b)

        assert result_a is False, "User A should be skipped"
        assert result_b is True, "User B should be processed"


class TestWebhookVerification:
    """Test webhook verification"""

    def test_verify_webhook_with_valid_token(self):
        """GIVEN mode=subscribe and token matches verify_token WHEN GET /whatsapp/webhook is called THEN return the challenge"""
        from src.bots import whatsapp_bot

        with patch("src.bots.whatsapp_bot.settings") as mock_settings:
            mock_settings.whatsapp_verify_token = "test_token"

            result = whatsapp_bot.verify_webhook(
                mode="subscribe", token="test_token", challenge="test_challenge"
            )

            assert result == "test_challenge"

    def test_reject_webhook_with_invalid_token(self):
        """GIVEN mode=subscribe but token doesn't match WHEN GET /whatsapp/webhook is called THEN return 403"""
        from src.bots import whatsapp_bot
        from fastapi import HTTPException

        with patch("src.bots.whatsapp_bot.settings") as mock_settings:
            mock_settings.whatsapp_verify_token = "test_token"

            with pytest.raises(HTTPException) as exc_info:
                whatsapp_bot.verify_webhook(
                    mode="subscribe", token="wrong_token", challenge="test_challenge"
                )

            assert exc_info.value.status_code == 403


class TestMessageHandling:
    """Test message handling"""

    @pytest.mark.asyncio
    async def test_process_text_message_successfully(self):
        """GIVEN a text message from user WHEN POST /whatsapp/webhook is called THEN response is sent via WhatsApp API"""
        from src.bots import whatsapp_bot

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "type": "text",
                                        "text": {"body": "I want shoes"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
            mock_handler.handle_message = AsyncMock(
                return_value="Here are some shoes for you"
            )
            with patch("src.bots.whatsapp_bot.send_whatsapp_message") as mock_send:
                mock_send.return_value = {"status": "success"}

                result = await whatsapp_bot.handle_webhook_payload(
                    payload, mock_handler, mock_send
                )

                mock_handler.handle_message.assert_called_once_with(
                    "I want shoes", platform="whatsapp"
                )
                mock_send.assert_called_once_with(
                    "+1234567890", "Here are some shoes for you"
                )

    @pytest.mark.asyncio
    async def test_process_interactive_message(self):
        """GIVEN an interactive message (button reply) WHEN POST /whatsapp/webhook is called THEN message body is extracted and processed"""
        from src.bots import whatsapp_bot

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "button_reply": {"id": "btn_shoes"}
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
            mock_handler.handle_message = AsyncMock(return_value="Processing button")
            with patch("src.bots.whatsapp_bot.send_whatsapp_message") as mock_send:
                mock_send.return_value = {"status": "success"}

                await whatsapp_bot.handle_webhook_payload(
                    payload, mock_handler, mock_send
                )

                mock_handler.handle_message.assert_called_once_with(
                    "btn_shoes", platform="whatsapp"
                )

    @pytest.mark.asyncio
    async def test_ignore_empty_message_array(self):
        """GIVEN webhook payload with no messages WHEN POST /whatsapp/webhook is called THEN return {"status": "ok"}"""
        from src.bots import whatsapp_bot

        payload = {"entry": [{"changes": [{"value": {"messages": []}}]}]}

        with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
            result = await whatsapp_bot.handle_webhook_payload(
                payload, mock_handler, AsyncMock()
            )

            assert result == {"status": "ok"}
            mock_handler.handle_message.assert_not_called()


class TestRetryLogic:
    """Test retry logic"""

    @pytest.mark.asyncio
    async def test_retry_on_chat_handler_failure(self):
        """GIVEN chat_handler raises exception WHEN handling message THEN retry up to 3 times with exponential backoff"""
        from src.bots import whatsapp_bot

        call_count = 0

        async def flaky_handler(msg, platform):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt failed")
            return "Success"

        mock_handler = MagicMock()
        mock_handler.handle_message = flaky_handler

        with patch("src.bots.whatsapp_bot.chat_handler", mock_handler):
            result = await whatsapp_bot.with_retry(
                mock_handler.handle_message, "test", platform="whatsapp"
            )

        assert call_count >= 2, "Should have retried after first failure"
        assert result == "Success"

    @pytest.mark.asyncio
    async def test_retry_on_whatsapp_api_failure(self):
        """GIVEN WhatsApp API returns error WHEN sending response THEN retry up to 3 times"""
        from src.bots import whatsapp_bot

        call_count = 0

        async def flaky_send(to, message):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("API error")
            return {"status": "success"}

        with patch("src.bots.whatsapp_bot.send_whatsapp_message") as mock_send:
            mock_send.side_effect = flaky_send

            result = await whatsapp_bot.with_retry(
                whatsapp_bot.send_whatsapp_message,
                "+1234567890",
                "Test message",
            )

        assert call_count >= 2, "Should have retried after first failure"

    @pytest.mark.asyncio
    async def test_log_error_after_all_retries_fail(self, caplog):
        """GIVEN all retry attempts fail WHEN handling message THEN log error with details"""
        from src.bots import whatsapp_bot

        async def always_fail(*args, **kwargs):
            raise Exception("Service unavailable")

        caplog.set_level(logging.ERROR)

        with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
            mock_handler.handle_message = always_fail

            await whatsapp_bot.handle_webhook_payload(
                {
                    "entry": [
                        {
                            "changes": [
                                {
                                    "value": {
                                        "messages": [
                                            {
                                                "from": "+1234567890",
                                                "type": "text",
                                                "text": {"body": "test"},
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                },
                mock_handler,
                AsyncMock(),
            )

            assert "error" in caplog.text.lower() or "unavailable" in caplog.text


class TestLogging:
    """Test logging functionality"""

    @pytest.mark.asyncio
    async def test_log_phone_number_and_message(self, caplog):
        """GIVEN a user sends a message WHEN webhook handles it THEN logger records phone number and message"""
        from src.bots import whatsapp_bot

        caplog.set_level(logging.INFO)

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "type": "text",
                                        "text": {"body": "I want shoes"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
            mock_handler.handle_message = AsyncMock(return_value="Response")
            with patch("src.bots.whatsapp_bot.send_whatsapp_message") as mock_send:
                mock_send.return_value = {"status": "success"}

                await whatsapp_bot.handle_webhook_payload(
                    payload, mock_handler, mock_send
                )

                assert "+1234567890" in caplog.text
                assert "I want shoes" in caplog.text

    @pytest.mark.asyncio
    async def test_log_response_time(self, caplog):
        """GIVEN a user sends a message WHEN webhook handles it THEN logger records how long processing took"""
        from src.bots import whatsapp_bot

        caplog.set_level(logging.INFO)

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "type": "text",
                                        "text": {"body": "test"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
            mock_handler.handle_message = AsyncMock(return_value="Response")
            with patch("src.bots.whatsapp_bot.send_whatsapp_message") as mock_send:
                mock_send.return_value = {"status": "success"}

                await whatsapp_bot.handle_webhook_payload(
                    payload, mock_handler, mock_send
                )

                assert (
                    "completed" in caplog.text.lower()
                    or "Response completed" in caplog.text
                )

    @pytest.mark.asyncio
    async def test_rate_limit_skip_no_response(self, caplog):
        """GIVEN user exceeds rate limit WHEN processing message THEN skip processing, no response sent, log warning"""
        from src.bots import whatsapp_bot

        caplog.set_level(logging.WARNING)

        limiter = RateLimiter(max_requests=10, window_seconds=60)
        for _ in range(10):
            limiter.record_search("+1234567890")

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "type": "text",
                                        "text": {"body": "test"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with patch("src.bots.whatsapp_bot.rate_limiter", limiter):
            with patch("src.bots.whatsapp_bot.chat_handler") as mock_handler:
                mock_handler.handle_message = AsyncMock()
                with patch("src.bots.whatsapp_bot.send_whatsapp_message") as mock_send:
                    result = await whatsapp_bot.handle_webhook_payload(
                        payload, mock_handler, mock_send
                    )

                    mock_handler.handle_message.assert_not_called()
                    mock_send.assert_not_called()
                    assert "rate limit" in caplog.text.lower()
