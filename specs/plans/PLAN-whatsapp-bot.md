# Plan: WhatsApp Bot

> **Date:** 2026-04-16
> **Project source:** PLAN-chatbot.md, Step 5
> **Estimated tasks:** 1
> **Planning session:** brief

## Summary

Update the existing WhatsApp bot webhook to add error handling with retry logic, rate limiting, and enhanced logging. The bot runs as a FastAPI webhook integrated into the main.py FastAPI app.

## Requirements

### Functional Requirements
1. Handle incoming WhatsApp messages via webhook (already exists)
2. Process messages through chat_handler.handle_message() (already exists)
3. Add retry with exponential backoff on chat handler failure
4. Add rate limiting (10 searches per minute per user)
5. Enhance logging with more detail

### Non-Functional Requirements
1. Retry: max 3 attempts with exponential backoff
2. Rate limiting: 10 searches/minute per user
3. Logging: user ID (phone number), message, response time, errors

## Behaviors

### Webhook Endpoints

**Why it matters:**
- GET /whatsapp/webhook verifies the webhook with Meta
- POST /whatsapp/webhook receives incoming messages

**What's required:**
- GET: Return challenge when mode=subscribe and token matches
- POST: Parse message, process through chat handler, send response

### Message Handling

**Why it matters:**
- Processes user queries and returns product recommendations

**What's required:**
- Parse user message from payload
- Call chat_handler.handle_message()
- Send response back to user via WhatsApp API

### Error Handling

**Why it matters:**
- Users shouldn't see failures when backend is temporarily unavailable

**What's required:**
- Retry with exponential backoff (max 3 attempts) for chat_handler
- Retry for WhatsApp API send failures
- Show no error to user (logging only) - WhatsApp requires quick response

### Rate Limiting

**Why it matters:**
- Prevents abuse and ensures fair usage

**What's required:**
- Track searches per user (by phone number)
- Limit to 10 searches per minute
- Skip processing if limit exceeded (don't respond)

### Logging

**Why it matters:**
- Debug issues and monitor bot health

**What's required:**
- Log phone number, message, response time
- Log errors with details

## Detailed Specifications

### WhatsApp Webhook

**Purpose:** Handle incoming WhatsApp messages and return product recommendations

**Interface:**
```python
router = APIRouter()
@router.get("/webhook")
@router.post("/webhook")
```

**Behavior:**
- Verify webhook on GET
- Handle messages on POST
- Send responses via WhatsApp API

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Chat handler fails | Retry up to 3 times, then log error |
| WhatsApp API fails | Retry up to 3 times, then log error |
| Rate limit exceeded | Skip processing, log warning |
| Invalid signature | Return 401 |

### Rate Limiter

**Purpose:** Track searches per user (phone number)

**Interface:**
```python
class RateLimiter:
    def is_allowed(user_id: str) -> bool:
    def record_search(user_id: str):
```

**Behavior:**
- Track last 10 searches per user in memory
- Reset counter after 1 minute
- Use phone number as user_id

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| WhatsApp requires quick response | Must respond within 20s, so don't block on retries for response sending |
| Phone number as user ID | WhatsApp uses phone numbers as user identifiers |
| Rate limit skips response | Don't send "too many requests" - just don't respond |

## Edge Cases & Failure Modes

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Chat handler unavailable | Retry 3 times, then log error | User-friendly, no crash |
| WhatsApp API fails | Retry 3 times, then log error | Ensure message delivery |
| Rate limit exceeded | Skip processing, don't respond | WhatsApp doesn't expect error response |
| Invalid signature | Return 401 | Security requirement |

## Decisions Log

| # | Decision | Alternatives Considered | Chosen Because |
|---|----------|------------------------|----------------|
| 1 | Rate limit by phone number | User ID, session | Phone number is WhatsApp's user identifier |
| 2 | Skip response on rate limit | Send "too many requests" message | WhatsApp API may block repeated messages |
| 3 | Retry WhatsApp send failures | Fail immediately | Better delivery reliability |

## Scope Boundaries

### In Scope
- Update existing webhook handlers
- Message handling with chat_handler
- Retry logic on failure (chat handler + API send)
- Rate limiting (10/min)
- Enhanced logging

### Out of Scope
- Telegram bot — already done (Step 4)
- Message templates — using simple text responses

## Dependencies

### Depends On (must exist before this work starts)
- FastAPI backend (Step 3) — chat_handler service
- Supabase (Step 1) — product data

### Depended On By (other work waiting for this)
- None

## Architecture Notes

The WhatsApp bot is a FastAPI router integrated into main.py with prefix "/whatsapp". It uses the same chat_handler service as the Telegram bot, but formats responses differently for WhatsApp platform.

## Open Questions (if any)

- None — all decisions resolved in this session

---

# Tasks

## Task T1: Add error handling, rate limiting, and logging to WhatsApp bot

> **Status:** done
> **Effort:** m
> **Priority:** high
> **Depends on:** None

### Description

Update the existing WhatsApp webhook in `src/bots/whatsapp_bot.py` to add:
- Retry logic with exponential backoff (max 3 attempts) for chat_handler and WhatsApp API
- In-memory rate limiting (10 searches per minute per phone number)
- Enhanced logging with phone number, message, response time, and errors

This makes the WhatsApp bot more robust and easier to debug.

### Test Plan

#### Test File(s)
- `tests/test_whatsapp_bot.py`

#### Test Scenarios

##### Webhook Verification

- **verify webhook with valid token** — GIVEN mode=subscribe and token matches verify_token WHEN GET /whatsapp/webhook is called THEN return the challenge
- **reject webhook with invalid token** — GIVEN mode=subscribe but token doesn't match WHEN GET /whatsapp/webhook is called THEN return 403

##### Message Handling

- **process text message successfully** — GIVEN a text message from user WHEN POST /whatsapp/webhook is called THEN response is sent via WhatsApp API
- **process interactive message** — GIVEN an interactive message (button reply) WHEN POST /whatsapp/webhook is called THEN message body is extracted and processed
- **ignore empty message array** — GIVEN webhook payload with no messages WHEN POST /whatsapp/webhook is called THEN return {"status": "ok"}

##### Retry Logic

- **retry on chat_handler failure** — GIVEN chat_handler raises exception WHEN handling message THEN retry up to 3 times with exponential backoff
- **retry on WhatsApp API failure** — GIVEN WhatsApp API returns error WHEN sending response THEN retry up to 3 times
- **log error after all retries fail** — GIVEN all retry attempts fail WHEN handling message THEN log error with details

##### Rate Limiting

- **allow 10 searches per minute** — GIVEN user sends 10 valid messages within 1 minute WHEN each message is processed THEN all 10 are processed
- **skip when rate limit exceeded** — GIVEN user sends 11 messages within 1 minute WHEN the 11th message is processed THEN processing is skipped, no response sent
- **separate limit per user** — GIVEN user A sends 10 messages, user B sends first message WHEN each message is processed THEN user A is skipped, user B is processed

##### Logging

- **log phone number and message** — GIVEN a user sends a message WHEN webhook handles it THEN logger records phone number and message
- **log response time** — GIVEN a user sends a message WHEN webhook handles it THEN logger records how long processing took
- **log errors** — GIVEN an error occurs WHEN handling message THEN logger records the error with details

### Implementation Notes

- **Layer(s):** FastAPI webhook router (src/bots/whatsapp_bot.py)
- **Pattern reference:** `src/bots/telegram_bot.py` for rate limiter and retry logic patterns, `src/bots/whatsapp_bot.py` for existing structure
- **Key decisions:**
  - Rate limit by phone number (WhatsApp's user identifier)
  - Skip response on rate limit (don't send "too many requests")
  - Retry both chat_handler and WhatsApp API failures
- **Libraries:** FastAPI, httpx, python-telegram-bot (already installed)

### Scope Boundaries

- Do NOT modify chat_handler service
- Do NOT add persistent rate limiting (database)
- Do NOT add message templates
- Only update the existing whatsapp_bot.py file and add tests

### Files Expected

**New files:**
- `tests/test_whatsapp_bot.py`

**Modified files:**
- `src/bots/whatsapp_bot.py` (add retry, rate limiter, logging)

**Must NOT modify:**
- `src/services/chat_handler.py` (not part of this task)
- `src/main.py` (already has router included)

### TDD Sequence

1. Write tests for RateLimiter class (independent)
2. Write tests for retry logic
3. Write tests for webhook verification and message handling
4. Write tests for logging
5. Implement the actual updates to make tests pass

---

_This task is ready for TDD implementation._
_Run: "Implement task T1 from specs/plans/PLAN-whatsapp-bot.md" (or use the /tdd skill)_