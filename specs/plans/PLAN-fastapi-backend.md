# Plan: FastAPI Backend

> **Date:** 2026-04-15
> **Project source:** PLAN-chatbot.md, Step 3
> **Estimated tasks:** 1
> **Planning session:** detailed

## Summary

Update the existing FastAPI backend to use Cohere for embeddings (instead of OpenAI), implement direct query approach with Supabase, add CORS restrictions based on environment, implement rate limiting, and add debugging headers. This is the core API layer that powers the Telegram and WhatsApp bots.

## Requirements

### Functional Requirements
1. Update search service to use Cohere embed-multilingual-v3.0 for embeddings
2. Replace Supabase RPC with direct query (execute_sql)
3. Implement intelligent filter parsing (price, category, gender from natural language)
4. Create unified ChatHandler service for both platforms

### Non-Functional Requirements
1. CORS: Dev (localhost, 127.0.0.1) | Prod (*.render.com, *.railway.com)
2. Rate limiting: 100 requests/minute per IP
3. Debugging headers: X-Request-ID, X-Response-Time
4. Handle Supabase unavailable: return empty results + error message
5. Handle Cohere partial failure: return partial results

## Behaviors

### Search Service

**Why it matters:**
- Vector embeddings enable semantic search (find products by meaning)
- Cohere provides 1024 dimensions, matching our database schema

**What's optional vs required:**
- Filter parsing is required for natural language queries
- Direct query approach preferred over RPC

**Common mistakes:**
- Using wrong embedding dimension (must match vector column)
- Not handling partial failures gracefully

### API Endpoints

**Why it matters:**
- /health for health checks
- /api/search for product search
- /api/chat for unified messaging

**What's optional vs required:**
- All three endpoints required
- WhatsApp webhook integrated

**Common mistakes:**
- Not validating input parameters
- Not handling errors gracefully

## Detailed Specifications

### SearchService

**Purpose:** Vector search with natural language filter parsing

**Interface:**
```python
class SearchService:
    async def search_products(
        query: str,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        limit: int = 3
    ) -> list[dict]:
```

**Behavior:**
- Generate query embedding using Cohere embed-multilingual-v3.0
- Execute direct SQL with cosine similarity
- Apply filters for price, category, gender
- Return top results ordered by similarity

**Validation Rules:**
- query: non-empty string
- max_price: positive float, optional
- category: one of [Fashion, Electronics, Home, Beauty], optional
- gender: one of [men, women, unisex], optional
- limit: positive integer, default 3, max 20

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Supabase unavailable | Return empty results + error in response |
| Cohere API fails partially | Return partial results |
| Invalid filter values | Ignore invalid, apply valid filters |
| Empty query | Return 400 Bad Request |

### Filter Parsing

**Purpose:** Extract filters from natural language queries

**Interface:**
```python
def parse_natural_language(query: str) -> dict:
    """Returns {query, max_price, category, gender}"""
```

**Behavior:**
- Extract price patterns: "under $100", "less than $50", "budget of $200"
- Extract gender: "men's", "women's", "for him", "for her"
- Extract category: keywords like "shoes", "headphones", "moisturizer"

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| No filters found | Return all filters as None |
| Ambiguous filters | Apply most likely filter |

### CORS Middleware

**Purpose:** Restrict cross-origin requests based on environment

**Behavior:**
- Dev: allow localhost, 127.0.0.1
- Prod: allow *.render.com, *.railway.com

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Origin not allowed | Return 403 Forbidden |

### Rate Limiting

**Purpose:** Prevent API abuse

**Behavior:**
- 100 requests/minute per IP
- Return 429 Too Many Requests when exceeded

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Rate limit exceeded | Return 429 with Retry-After header |

### Debugging Headers

**Purpose:** Help with API debugging and monitoring

**Behavior:**
- X-Request-ID: UUID for each request
- X-Response-Time: time in milliseconds

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| Cohere embed-multilingual-v3.0 1024 dims | Must match database vector column |
| Rate limit 100/min | Prevents abuse while allowing正常使用 |
| Direct query approach | Simpler than RPC, no function setup needed |

## Edge Cases & Failure Modes

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Supabase unavailable | Return empty + error message | User-friendly, allows retry |
| Cohere partial failure | Return partial results | Graceful degradation |
| Empty search results | Return "no results" message | Keep existing behavior |
| Rate limit exceeded | Return 429 with Retry-After | Standard HTTP approach |
| Invalid origin | Return 403 | Security enforcement |

## Decisions Log

| # | Decision | Alternatives Considered | Chosen Because |
|---|----------|------------------------|----------------|
| 1 | Use Cohere for embeddings | OpenAI (paid) | Free tier, matches Step 1 decision |
| 2 | Direct query approach | RPC, Query builder | Simpler than RPC, no function setup |
| 3 | CORS by environment | Allow all | Security best practice |
| 4 | Rate limit 100/min | 30, 60 | Reasonable for demo usage |
| 5 | Add debug headers | None | Better debugging capability |

## Scope Boundaries

### In Scope
- Update search service to use Cohere
- Implement direct query approach
- CORS restrictions by environment
- Rate limiting (100/min)
- Debugging headers
- Update chat handler if needed

### Out of Scope
- Telegram bot code — separate feature (Step 4)
- WhatsApp bot code — separate feature (Step 5)
- Authentication/authorization — not required for demo

## Dependencies

### Depends On (must exist before this work starts)
- Supabase setup (Step 1) — products table with vector(1024)
- Data ingestion (Step 2) — products in database

### Depended On By (other work waiting for this)
- Telegram bot (Step 4) — calls API endpoints
- WhatsApp bot (Step 5) — calls API endpoints

## Architecture Notes

This is the API layer for the chatbot. It provides REST endpoints that the bots call. Uses FastAPI with pydantic for validation. Follows existing patterns from src/main.py and src/services/.

## Open Questions (if any)

- None — all decisions resolved in this session

---
_This plan is the input for the generate-tasks skill._
_Review this document, then run: "Generate task from plan: specs/plans/PLAN-fastapi-backend.md"_

---

# Tasks

## Task T1: FastAPI Backend Update

> **Status:** done
> **Effort:** m
> **Priority:** high
> **Depends on:** None

### Description

Update the FastAPI backend to use Cohere for embeddings (instead of OpenAI), implement direct query approach with Supabase, add CORS restrictions based on environment, implement rate limiting (100/min), and add debugging headers (X-Request-ID, X-Response-Time). This is the core API layer that powers the Telegram and WhatsApp bots.

### Test Plan

#### Test File(s)
- `tests/test_search_service.py` (new file)
- `tests/test_api_endpoints.py` (new file)
- `tests/test_filter_parsing.py` (new file)

#### Test Scenarios

##### Search Service

- **uses Cohere for embeddings** — GIVEN a query WHEN search_products THEN Cohere API is called
- **returns products from database** — GIVEN valid query WHEN search THEN returns product list
- **applies max_price filter** — GIVEN max_price=50 WHEN search THEN all results price <= 50
- **applies category filter** — GIVEN category="Fashion" WHEN search THEN all results category=Fashion
- **applies gender filter** — GIVEN gender="men" WHEN search THEN all results gender=men or unisex
- **returns empty on Supabase failure** — GIVEN Supabase unavailable WHEN search THEN returns empty results with error

##### Filter Parsing

- **extracts price from "under $100"** — GIVEN "shoes under $100" WHEN parse THEN max_price=100
- **extracts gender from "men's"** — GIVEN "men's shoes" WHEN parse THEN gender="men"
- **extracts category from keywords** — GIVEN "wireless headphones" WHEN parse THEN category="Electronics"

##### API Endpoints

- **/health returns ok** — WHEN GET /health THEN returns {"status": "ok"}
- **/api/search accepts valid request** — WHEN POST /api/search with valid body THEN returns ChatResponse
- **returns 400 on empty query** — WHEN POST /api/search with empty query THEN returns 400

##### CORS

- **allows localhost in dev** — GIVEN Origin: http://localhost WHEN request THEN allows
- **blocks unknown origin** — GIVEN Origin: http://evil.com WHEN request THEN returns 403

##### Rate Limiting

- **blocks after 100 requests** — GIVEN 101 requests in 1 minute WHEN request THEN returns 429

##### Debug Headers

- **includes X-Request-ID** — WHEN request THEN response has X-Request-ID header
- **includes X-Response-Time** — WHEN request THEN response has X-Response-Time header

### Implementation Notes

- **Layer:** API (FastAPI)
- **Pattern reference:** Existing src/main.py, src/services/search_service.py
- **Key decisions:**
  - Cohere embed-multilingual-v3.0 (1024 dimensions)
  - Direct query approach (execute_sql)
  - CORS: Dev (localhost, 127.0.0.1) | Prod (*.render.com, *.railway.com)
  - Rate limit: 100 requests/minute
- **Libraries:** fastapi, slowapi (rate limiting), cohere

### Scope Boundaries

- Do NOT modify Telegram bot code — separate feature (Step 4)
- Do NOT modify WhatsApp bot code — separate feature (Step 5)
- Do NOT add authentication/authorization — not required for demo

### Files Expected

**New files:**
- `tests/test_search_service.py`
- `tests/test_api_endpoints.py`
- `tests/test_filter_parsing.py`

**Modified files:**
- `src/services/search_service.py` (use Cohere, direct query)
- `src/main.py` (CORS, rate limiting, debug headers)
- `src/config.py` (add COHERE_API_KEY)

**Must NOT modify:**
- None

### TDD Sequence

1. Test filter parsing (unit) — parse_natural_language function
2. Test search service (unit + integration) — search_products function
3. Test API endpoints (integration) — /health, /api/search, /api/chat
4. Test CORS and rate limiting (integration)