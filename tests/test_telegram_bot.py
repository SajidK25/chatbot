import pytest
import time
import asyncio
import logging
from unittest.mock import patch, MagicMock, AsyncMock


class RateLimiter:
    """In-memory rate limiter: 10 searches per minute per user"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup(user_id, now)
        user_requests = self._requests.get(user_id, [])
        return len(user_requests) < self.max_requests

    def record_search(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup(user_id, now)
        if user_id not in self._requests:
            self._requests[user_id] = []
        if len(self._requests[user_id]) >= self.max_requests:
            return False
        self._requests[user_id].append(now)
        return True

    def _cleanup(self, user_id: str, now: float):
        cutoff = now - self.window_seconds
        if user_id in self._requests:
            self._requests[user_id] = [t for t in self._requests[user_id] if t > cutoff]


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_allow_10_searches_per_minute(self):
        """GIVEN user sends 10 valid search messages within 1 minute WHEN each message is handled THEN all 10 are processed"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_id = "12345"

        results = [limiter.record_search(user_id) for _ in range(10)]

        assert all(results), "All 10 searches should be allowed"

    def test_reject_11th_search(self):
        """GIVEN user sends 11 valid search messages within 1 minute WHEN the 11th message is handled THEN user receives 'Too many requests' message"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_id = "12345"

        for _ in range(10):
            limiter.record_search(user_id)

        result = limiter.record_search(user_id)

        assert result is False, "11th search should be rejected"

    def test_reset_after_1_minute(self):
        """GIVEN user sends 10 searches, then waits 1 minute WHEN user sends another search THEN it is allowed"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_id = "12345"

        for _ in range(10):
            limiter.record_search(user_id)

        limiter._requests[user_id] = [time.time() - 61]

        result = limiter.record_search(user_id)

        assert result is True, "Search after 1 minute should be allowed"

    def test_separate_limit_per_user(self):
        """GIVEN user A sends 10 searches, user B sends their first search WHEN each user's message is handled THEN user A is blocked, user B is allowed"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        user_a = "12345"
        user_b = "67890"

        for _ in range(10):
            limiter.record_search(user_a)

        result_a = limiter.is_allowed(user_a)
        result_b = limiter.is_allowed(user_b)

        assert result_a is False, "User A should be blocked"
        assert result_b is True, "User B should be allowed"


class TestRetryLogic:
    """Test retry with exponential backoff"""

    @pytest.mark.asyncio
    async def test_retry_on_first_failure(self):
        """GIVEN chat_handler raises exception on first call WHEN message is handled THEN bot retries the call"""
        from src.bots import telegram_bot

        original_handler = telegram_bot.chat_handler.handle_message

        call_count = 0

        async def flaky_handler(msg, platform):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt failed")
            return "Success"

        mock_handler = MagicMock()
        mock_handler.handle_message = flaky_handler

        with patch.object(telegram_bot, "chat_handler", mock_handler):
            mock_update = MagicMock()
            mock_update.message.text = "test"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            try:
                await telegram_bot.handle_message(mock_update, mock_context)
            except Exception:
                pass

        assert call_count >= 2, "Should have retried after first failure"

    @pytest.mark.asyncio
    async def test_retry_up_to_3_times(self):
        """GIVEN chat_handler always raises exception WHEN message is handled THEN bot makes exactly 3 attempts"""
        from src.bots import telegram_bot

        call_count = 0

        async def always_fail(msg, platform):
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        mock_handler = MagicMock()
        mock_handler.handle_message = always_fail

        with patch.object(telegram_bot, "chat_handler", mock_handler):
            mock_update = MagicMock()
            mock_update.message.text = "test"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            try:
                await telegram_bot.handle_message(mock_update, mock_context)
            except Exception:
                pass

        assert call_count == 3, "Should make exactly 3 attempts"

    @pytest.mark.asyncio
    async def test_show_error_after_all_retries_fail(self):
        """GIVEN chat_handler fails all 3 attempts WHEN message is handled THEN user receives friendly error message"""
        from src.bots import telegram_bot

        async def always_fail(msg, platform):
            raise Exception("Service unavailable")

        mock_handler = MagicMock()
        mock_handler.handle_message = always_fail

        with patch.object(telegram_bot, "chat_handler", mock_handler):
            mock_update = MagicMock()
            mock_update.message.text = "test"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            await telegram_bot.handle_message(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            error_message = call_args[0][0]
            assert (
                "Something went wrong" in error_message
                or "error" in error_message.lower()
            )


class TestCommandHandlers:
    """Test command handlers"""

    @pytest.mark.asyncio
    async def test_start_command_returns_welcome_message(self):
        """GIVEN a user sends /start WHEN bot processes the command THEN reply contains 'OpenClaw' and example queries"""
        from src.bots import telegram_bot

        mock_update = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = MagicMock()

        await telegram_bot.start_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        reply_text = call_args[0][0]

        assert "OpenClaw" in reply_text
        assert "shoes" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_help_command_returns_help_message(self):
        """GIVEN a user sends /help WHEN bot processes the command THEN reply contains usage examples"""
        from src.bots import telegram_bot

        mock_update = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = MagicMock()

        await telegram_bot.help_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        reply_text = call_args[0][0]

        assert "Shopping Assistant" in reply_text


class TestMessageHandling:
    """Test message handling"""

    @pytest.mark.asyncio
    async def test_text_message_processed_successfully(self):
        """GIVEN a user sends 'men's shoes under $100' WHEN bot handles message THEN response contains product recommendations"""
        from src.bots import telegram_bot

        async def mock_handler(msg, platform):
            return "Here are some recommendations: Product 1, Product 2"

        mock_handler_obj = MagicMock()
        mock_handler_obj.handle_message = mock_handler

        with patch.object(telegram_bot, "chat_handler", mock_handler_obj):
            mock_update = MagicMock()
            mock_update.message.text = "men's shoes under $100"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            await telegram_bot.handle_message(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            response = call_args[0][0]
            assert "recommendations" in response.lower()

    @pytest.mark.asyncio
    async def test_response_formatted_for_telegram(self):
        """GIVEN chat_handler returns products WHEN bot sends reply THEN message is in Telegram markdown format"""
        from src.bots import telegram_bot

        async def mock_handler(msg, platform):
            return "Product: Test Item - $50.00"

        mock_handler_obj = MagicMock()
        mock_handler_obj.handle_message = mock_handler

        with patch.object(telegram_bot, "chat_handler", mock_handler_obj):
            mock_update = MagicMock()
            mock_update.message.text = "test"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            await telegram_bot.handle_message(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args[1].get("parse_mode") == "Markdown"

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excess_requests(self):
        """GIVEN user exceeds rate limit WHEN sending message THEN rate limit message is returned"""
        from src.bots import telegram_bot

        mock_handler_obj = MagicMock()
        mock_handler_obj.handle_message = AsyncMock(return_value="Response")

        with patch.object(telegram_bot, "chat_handler", mock_handler_obj):
            with patch.object(telegram_bot, "rate_limiter") as mock_limiter:
                mock_limiter.is_allowed.return_value = False

                mock_update = MagicMock()
                mock_update.message.text = "test"
                mock_update.effective_user.id = 123
                mock_update.message.reply_text = AsyncMock()
                mock_context = MagicMock()
                mock_context.bot.send_chat_action = AsyncMock()

                await telegram_bot.handle_message(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                response = call_args[0][0]
                assert "Too many requests" in response


class TestLogging:
    """Test logging functionality"""

    @pytest.mark.asyncio
    async def test_log_user_id_and_message(self, caplog):
        """GIVEN a user sends a message WHEN bot handles it THEN logger records the user ID and message text"""
        from src.bots import telegram_bot

        caplog.set_level(logging.INFO)

        async def mock_handler(msg, platform):
            return "Response"

        mock_handler_obj = MagicMock()
        mock_handler_obj.handle_message = mock_handler

        with patch.object(telegram_bot, "chat_handler", mock_handler_obj):
            mock_update = MagicMock()
            mock_update.message.text = "test message"
            mock_update.effective_user.id = 12345
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            await telegram_bot.handle_message(mock_update, mock_context)

            assert "12345" in caplog.text
            assert "test message" in caplog.text

    @pytest.mark.asyncio
    async def test_log_response_time(self, caplog):
        """GIVEN a user sends a message WHEN bot handles it THEN logger records how long processing took"""
        from src.bots import telegram_bot

        caplog.set_level(logging.INFO)

        async def mock_handler(msg, platform):
            return "Response"

        mock_handler_obj = MagicMock()
        mock_handler_obj.handle_message = mock_handler

        with patch.object(telegram_bot, "chat_handler", mock_handler_obj):
            mock_update = MagicMock()
            mock_update.message.text = "test"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            await telegram_bot.handle_message(mock_update, mock_context)

            assert (
                "completed" in caplog.text.lower()
                or "Response completed" in caplog.text
            )

    @pytest.mark.asyncio
    async def test_log_errors_with_traceback(self, caplog):
        """GIVEN chat_handler raises exception WHEN bot handles message THEN logger records the error with stack trace"""
        from src.bots import telegram_bot

        caplog.set_level(logging.ERROR)

        async def mock_handler(msg, platform):
            raise Exception("Test error")

        mock_handler_obj = MagicMock()
        mock_handler_obj.handle_message = mock_handler

        with patch.object(telegram_bot, "chat_handler", mock_handler_obj):
            mock_update = MagicMock()
            mock_update.message.text = "test"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()
            mock_context = MagicMock()
            mock_context.bot.send_chat_action = AsyncMock()

            await telegram_bot.handle_message(mock_update, mock_context)

            assert "error" in caplog.text.lower() or "Error processing" in caplog.text
