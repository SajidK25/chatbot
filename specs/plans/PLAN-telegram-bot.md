# Plan: Telegram Bot

> **Date:** 2026-04-15
> **Project source:** PLAN-chatbot.md, Step 4
> **Estimated tasks:** 1
> **Planning session:** detailed

## Summary

Update the existing Telegram bot to add error handling with retry logic, rate limiting, and enhanced logging. The bot uses direct calls to chat_handler (no HTTP), which is simpler for the demo.

## Requirements

### Functional Requirements
1. Update bot to use existing /start and /help commands
2. Handle messages via chat_handler.handle_message()
3. Add retry with exponential backoff on chat handler failure
4. Add rate limiting (10 searches per minute per user)
5. Enhance logging with more detail

### Non-Functional Requirements
1. Retry: max 3 attempts with exponential backoff
2. Rate limiting: 10 searches/minute per user
3. Logging: user ID, message, response time, errors

## Behaviors

### Command Handlers

**Why it matters:**
- /start introduces the bot to new users
- /help provides usage instructions

**What's required:**
- /start: Welcome message with examples
- /help: Help message with examples

### Message Handling

**Why it matters:**
- Processes user queries and returns product recommendations

**What's required:**
- Parse user message
- Call chat_handler.handle_message()
- Send response back to user

### Error Handling

**Why it matters:**
- Users shouldn't see crashes when backend fails

**What's required:**
- Retry with exponential backoff (max 3 attempts)
- Show friendly error message if all retries fail

### Rate Limiting

**Why it matters:**
- Prevents abuse and ensures fair usage

**What's required:**
- Track searches per user
- Limit to 10 searches per minute
- Show "Too many requests" message when exceeded

### Logging

**Why it matters:**
- Debug issues and monitor bot health

**What's required:**
- Log user ID, message, response time
- Log errors with stack traces

## Detailed Specifications

### Telegram Bot

**Purpose:** Handle user messages and return product recommendations

**Interface:**
```python
def run_telegram_bot():
    """Run the Telegram bot"""
```

**Behavior:**
- Start polling for updates
- Handle /start command
- Handle /help command
- Handle text messages

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Chat handler fails | Retry up to 3 times, then show error |
| Rate limit exceeded | Show "Try again later" message |
| Invalid message type | Ignore |

### Rate Limiter

**Purpose:** Track searches per user

**Interface:**
```python
class RateLimiter:
    def is_allowed(user_id: str) -> bool:
    def record_search(user_id: str):
```

**Behavior:**
- Track last 10 searches per user in memory
- Reset counter after 1 minute

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Memory limit reached | Reset oldest entries |

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| Direct chat_handler call | Simpler for demo, no HTTP overhead |
| 10 searches/min limit | Prevents abuse, fair usage |
| Retry max 3 times | Prevents infinite loops, gives up gracefully |

## Edge Cases & Failure Modes

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Chat handler unavailable | Retry 3 times, then show error | User-friendly, no crashes |
| Rate limit exceeded | Show friendly message | Clear feedback |
| Invalid message type | Ignore silently | Don't crash on non-text |

## Decisions Log

| # | Decision | Alternatives Considered | Chosen Because |
|---|----------|------------------------|----------------|
| 1 | Direct chat_handler call | HTTP to backend | Simpler, no network dependency |
| 2 | Text-only responses | Include images | Faster, simpler for demo |
| 3 | Rate limit 10/min | 30, 60, unlimited | Reasonable for demo |
| 4 | Retry with backoff | Fail immediately | Better user experience |

## Scope Boundaries

### In Scope
- Update existing /start and /help commands
- Message handling with chat_handler
- Retry logic on failure
- Rate limiting (10/min)
- Enhanced logging

### Out of Scope
- WhatsApp bot — separate feature (Step 5)
- Adding images to responses — text-only for now

## Dependencies

### Depends On (must exist before this work starts)
- FastAPI backend (Step 3) — chat_handler service
- Supabase (Step 1) — product data

### Depended On By (other work waiting for this)
- None

## Architecture Notes

The bot runs as a standalone process using python-telegram-bot v21+. It uses direct function calls to chat_handler (same process) rather than HTTP calls. This is simpler and has lower latency.

## Open Questions (if any)

- None — all decisions resolved in this session

---

# Tasks

## Task T1: Add error handling, rate limiting, and logging to Telegram bot

> **Status:** done
> **Effort:** m
> **Priority:** high
> **Depends on:** None

### Description

Update the existing Telegram bot in `src/bots/telegram_bot.py` to add:
- Retry logic with exponential backoff (max 3 attempts) when chat_handler fails
- In-memory rate limiting (10 searches per minute per user)
- Enhanced logging with user ID, message, response time, and errors

This makes the bot more robust and easier to debug.

### Test Plan

#### Test File(s)
- `tests/test_telegram_bot.py`

#### Test Scenarios

##### Command Handlers

- **start command returns welcome message** — GIVEN a user sends /start WHEN bot processes the command THEN reply contains "OpenClaw" and example queries
- **help command returns help message** — GIVEN a user sends /help WHEN bot processes the command THEN reply contains usage examples

##### Message Handling

- **text message processed successfully** — GIVEN a user sends "men's shoes under $100" WHEN bot handles message THEN response contains product recommendations
- **response formatted for telegram** — GIVEN chat_handler returns products WHEN bot sends reply THEN message is in Telegram markdown format

##### Retry Logic

- **retry on first failure** — GIVEN chat_handler raises exception on first call WHEN message is handled THEN bot retries the call
- **retry up to 3 times** — GIVEN chat_handler always raises exception WHEN message is handled THEN bot makes exactly 3 attempts
- **show error after all retries fail** — GIVEN chat_handler fails all 3 attempts WHEN message is handled THEN user receives friendly error message
- **exponential backoff between retries** — GIVEN chat_handler fails first call, succeeds second call WHEN message is handled THEN there is increasing delay between attempts

##### Rate Limiting

- **allow 10 searches per minute** — GIVEN user sends 10 valid search messages within 1 minute WHEN each message is handled THEN all 10 are processed
- **reject 11th search** — GIVEN user sends 11 valid search messages within 1 minute WHEN the 11th message is handled THEN user receives "Too many requests" message
- **reset after 1 minute** — GIVEN user sends 10 searches, then waits 1 minute WHEN user sends another search THEN it is allowed
- **separate limit per user** — GIVEN user A sends 10 searches, user B sends their first search WHEN each user's message is handled THEN user A is blocked, user B is allowed

##### Logging

- **log user ID and message** — GIVEN a user sends a message WHEN bot handles it THEN logger records the user ID and message text
- **log response time** — GIVEN a user sends a message WHEN bot handles it THEN logger records how long processing took
- **log errors with traceback** — GIVEN chat_handler raises exception WHEN bot handles message THEN logger records the error with stack trace

### Implementation Notes

- **Layer(s):** Bot handlers (src/bots/telegram_bot.py)
- **Pattern reference:** `src/bots/telegram_bot.py` for existing structure, `tests/test_api_endpoints.py` for test patterns
- **Key decisions:**
  - In-memory rate limiting (simpler for demo)
  - Direct chat_handler call (no HTTP)
  - Text-only responses
- **Libraries:** python-telegram-bot v21+, standard library (collections, time, logging)

### Scope Boundaries

- Do NOT modify chat_handler service
- Do NOT add persistent rate limiting (database)
- Do NOT add image support to responses
- Only update the existing telegram_bot.py file and add tests

### Files Expected

**New files:**
- `tests/test_telegram_bot.py`

**Modified files:**
- `src/bots/telegram_bot.py` (add retry, rate limiter, logging)

**Must NOT modify:**
- `src/services/chat_handler.py` (not part of this task)
- `src/main.py` (not part of this task)

### TDD Sequence

1. Write tests for rate limiter class first (independent)
2. Write tests for retry logic
3. Write tests for command handlers and message handling
4. Implement the actual bot updates to make tests pass

---

_This task is ready for TDD implementation._
_Run: "Implement task T1 from specs/plans/PLAN-telegram-bot.md" (or use the /tdd skill)_