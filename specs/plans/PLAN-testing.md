# Plan: Testing & Refinement

> **Date:** 2026-04-16
> **Project source:** PLAN-chatbot.md, Step 6
> **Estimated tasks:** 1
> **Planning session:** brief

## Summary

Run integration tests against the 5 sample queries to verify semantic search quality and ensure both Telegram and WhatsApp flows work correctly.

## Requirements

### Functional Requirements
1. Run 5 sample queries against the search API
2. Verify semantic search quality
3. Check Telegram flow produces correct response format
4. Check WhatsApp flow produces correct response format

### Test Queries
| # | Test Query | Expected Behavior |
|---|------------|-------------------|
| 1 | "men's shoes under $100" | Returns men's shoes, price ≤ $100, uses vector similarity |
| 2 | "red wireless headphones under 50 dollars" | Returns red wireless headphones ≤ $50 |
| 3 | "best running shoes for women" | Returns women's running shoes ranked by relevance |
| 4 | "moisturizer for dry skin" | Returns beauty category moisturizers |
| 5 | "cheap bluetooth speaker" | Returns electronics/speakers with lower prices |

## Testing Approach

### Unit Tests (can run now)
- Filter parsing tests (already exists in test_filter_parsing.py)
- API endpoint tests (already exists in test_api_endpoints.py)
- Telegram bot tests (already exists in test_telegram_bot.py)
- WhatsApp bot tests (already exists in test_whatsapp_bot.py)

### Integration Tests (requires environment)
- Run actual queries against the search_service
- Verify response contains expected products
- Check price filters are applied correctly
- Verify category extraction works

## Scope Boundaries

### In Scope
- Run all unit tests (56 tests)
- Verify no test failures

### Out of Scope
- Actual API deployment testing (Step 7)
- End-to-end manual testing with real Telegram/WhatsApp

## Dependencies

### Depends On (must exist before this work starts)
- Steps 1-5 complete (Supabase, Data Ingestion, FastAPI, Telegram, WhatsApp)

### Depended On By (other work waiting for this)
- Step 7: Deployment

## Open Questions (if any)

- None — this is a verification step

---

# Tasks

## Task T1: Run unit tests and verify all pass

> **Status:** in progress
> **Effort:** xs
> **Priority:** critical
> **Depends on:** None

### Description

Run all 56 unit tests to verify the implementation is working correctly. This is a quick verification step before deployment.

### Test Plan

#### Test File(s)
- All test files in `tests/` directory

#### Test Scenarios

- **all tests pass** — GIVEN all test files exist WHEN pytest is run THEN all 56 tests pass

### Implementation Notes

- **Layer(s):** All layers
- **Pattern reference:** tests/test_*.py for existing test patterns
- Run with: `uv run python -m pytest tests/ -v`

### Files Expected

**No new files expected - this is a verification task**

---

_This task is ready for TDD implementation._
_Run: "Implement task T1 from specs/plans/PLAN-testing.md" (or use the /tdd skill)_