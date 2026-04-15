# Plan: Data Ingestion Script

> **Date:** 2026-04-15
> **Project source:** PLAN-chatbot.md, Step 2
> **Estimated tasks:** 1
> **Planning session:** detailed

## Summary

Build a reusable data ingestion script that generates realistic product data with embeddings and inserts them into Supabase. The script uses Cohere's free embedding model (1024 dimensions), supports configurable product counts, handles duplicate products via upsert, and includes robust error handling with retry logic.

## Requirements

### Functional Requirements
1. Generate configurable number of realistic products (default: 500)
2. Products distributed across 4 categories: Fashion, Electronics, Home, Beauty
3. Each product has: name, description, price, category, image_url, product_url, brand, gender
4. Generate combined text for embeddings (name + description + brand + category)
5. Generate embeddings using Cohere embed-multilingual-v3.0 (1024 dimensions)
6. Insert products into Supabase with async batching
7. Upsert products based on name + brand combination
8. Reusable script - can run multiple times to add more products

### Non-Functional Requirements
1. Cohere API: retry with exponential backoff on failure
2. Rate limiting: add delay between batches
3. Partial failure handling: continue with successful inserts, log failures
4. Default batch size: 50 for embedding and insert operations

## Behaviors

### Product Generation

**Why it matters:**
- Realistic product data enables meaningful semantic search testing
- Multiple categories ensure diverse search results
- Gender field enables filtered searches

**What's optional vs required:**
- Product count is configurable; default 500 is sufficient for demo
- Gender can be null (unisex products)

**Common mistakes:**
- Hard-coding product count instead of making it configurable
- Not combining text fields for embedding (loses context)

### Embedding Generation

**Why it matters:**
- Vector embeddings enable semantic search (find products by meaning, not just keywords)
- Cohere free tier provides 1M tokens/month

**What's optional vs required:**
- Batch size is configurable; 100 is a good default
- Delay between batches prevents rate limiting

**Common mistakes:**
- Using wrong embedding dimension (must match vector column in DB)
- Not handling API errors gracefully

### Database Insertion

**Why it matters:**
- Upsert ensures idempotent runs (can re-run without duplicating)
- Async batching improves performance

**What's optional vs required:**
- Batch size configurable; 50 is a good default

**Common mistakes:**
- Not handling partial failures (losing good data when one insert fails)
- Not using upsert (creates duplicates on re-runs)

## Detailed Specifications

### Product Generator

**Purpose:** Generate realistic product data

**Interface:**
```python
def generate_products(count: int) -> list[dict]:
    """Generate count products across categories"""
```

**Behavior:**
- Randomly select category, brand, and item type
- Combine gender (men/women/unisex/null) with item name
- Generate realistic price based on category
- Generate image_url using picsum.photos
- Generate product_url with unique product ID

**Validation Rules:**
- name: non-empty string
- description: non-empty string
- price: positive decimal
- category: one of [Fashion, Electronics, Home, Beauty]
- image_url: valid URL format
- product_url: valid URL format
- brand: non-empty string
- gender: nullable (men, women, unisex, None)

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Empty product count | Use default 500 |
| Invalid category | Skip product, log warning |

### Embedding Generator

**Purpose:** Generate vector embeddings for products

**Interface:**
```python
async def generate_embeddings(products: list[dict], client: AsyncCohere) -> list[dict]:
    """Add embedding to each product"""
```

**Behavior:**
- Combine text: f"{name}. {description}. {brand}. {category}"
- Batch requests (default 100 per batch)
- Add delay between batches (prevent rate limiting)
- Retry failed requests with exponential backoff

**Validation Rules:**
- Embedding dimension must be 1024

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Cohere API timeout | Retry up to 3 times with exponential backoff |
| Invalid API key | Raise error, stop execution |
| Rate limited (429) | Wait and retry |

### Database Inserter

**Purpose:** Insert products into Supabase

**Interface:**
```python
async def insert_products(products: list[dict], supabase: AsyncClient):
    """Insert/upsert products into database"""
```

**Behavior:**
- Batch insert (default 50 per batch)
- Upsert based on name + brand (unique constraint)
- Continue on partial failure, log failures

**Validation Rules:**
- All required fields must be present
- Embedding must be vector(1024)

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Database connection failed | Raise error, stop execution |
| Partial batch failure | Continue with successful inserts, log failed items |
| Invalid vector dimension | Skip product, log error |

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| Embedding dimension 1024 | Must match Supabase column definition |
| Upsert on name + brand | Prevents duplicates on re-runs |
| Retry with backoff | Handles temporary API failures |
| Batch delay | Prevents rate limiting |

## Edge Cases & Failure Modes

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Cohere API unavailable | Retry 3 times with exponential backoff | Transient failures should recover |
| All retries exhausted | Log error, exit with failure code | Don't proceed with incomplete data |
| Some inserts fail | Continue with successful, log failures | Don't lose good data |
| Duplicate product on re-run | Upsert (update existing) | Maintains data consistency |
| Zero products requested | Use default 500 | Sensible default |

## Decisions Log

| # | Decision | Alternatives Considered | Chosen Because |
|---|----------|------------------------|----------------|
| 1 | Use Cohere embed-multilingual-v3.0 | OpenAI (paid), Sentence Transformers (local) | Free tier (1M tokens/month), similar API to OpenAI |
| 2 | Default 500 products | 100, 1000 | 500 provides good search diversity without being slow |
| 3 | Upsert on name + brand | Clear table, append only | Reusable, idempotent |
| 4 | Retry with exponential backoff | Fail immediately, infinite retry | Balances reliability with not hanging forever |
| 5 | Continue on partial failure | Rollback all | Don't lose successful inserts |

## Scope Boundaries

### In Scope
- Product generation logic
- Embedding generation with Cohere
- Supabase insertion with upsert
- Error handling and retry logic
- Configurable via command line arguments

### Out of Scope
- Database schema creation — separate feature (Step 1)
- API endpoint code — separate feature (Step 3)
- Telegram/WhatsApp bot code — separate features (Steps 4-5)

## Dependencies

### Depends On (must exist before this work starts)
- Supabase setup (Step 1) — products table with vector(1024) column
- Cohere API key — for embedding generation

### Depended On By (other work waiting for this)
- FastAPI backend (Step 3) — needs products in database for search
- Bot integration (Steps 4-5) — needs search functionality

## Architecture Notes

This script is a standalone utility, not part of the API. It runs independently to populate the database. Uses async/await for concurrent API calls. Follows the existing project patterns from PLAN-chatbot.md and the existing ingest_products.py structure.

## Open Questions (if any)

- None — all decisions resolved in this session

---
_This plan is the input for the generate-tasks skill._
_Review this document, then run: "Generate task from plan: specs/plans/PLAN-data-ingestion.md"_

---

# Tasks

## Task T1: Data Ingestion Script Implementation

> **Status:** done
> **Effort:** m
> **Priority:** high
> **Depends on:** None

### Description

Implement a reusable data ingestion script that generates realistic product data with Cohere embeddings and inserts them into Supabase. Supports configurable product counts, handles duplicate products via upsert, and includes robust error handling with retry logic.

### Test Plan

#### Test File(s)
- `tests/test_ingest_products.py` (new file)
- `tests/test_product_generator.py` (new file)
- `tests/test_embedding_generator.py` (new file)

#### Test Scenarios

##### Product Generation

- **generates correct number of products** — GIVEN count=10 WHEN generate_products(10) THEN returns 10 products
- **products have required fields** — GIVEN any product WHEN generated THEN has name, description, price, category, image_url, product_url, brand, gender
- **products distributed across categories** — GIVEN count=100 WHEN generated THEN all 4 categories (Fashion, Electronics, Home, Beauty) represented
- **price ranges realistic per category** — GIVEN Fashion product THEN price between $15-$200

##### Embedding Generation

- **generates 1024-dimensional embeddings** — GIVEN product WHEN embed THEN embedding length is 1024
- **combines text correctly** — GIVEN product WHEN embed THEN text includes name, description, brand, category
- **retries on API failure** — GIVEN Cohere API timeout WHEN embed THEN retries up to 3 times with exponential backoff

##### Database Insertion

- **inserts products into Supabase** — GIVEN products WHEN insert THEN products in database
- **upserts on duplicate** — GIVEN existing product (name+brand) WHEN insert THEN updates instead of creating duplicate
- **continues on partial failure** — GIVEN some inserts fail WHEN insert THEN continues with successful, logs failures

##### Edge Cases

- **zero count uses default** — GIVEN count=0 WHEN generate THEN uses default 500
- **negative count uses default** — GIVEN count=-5 WHEN generate THEN uses default 500
- **all retries exhausted logs error** — GIVEN Cohere API fails 3 times THEN logs error, exits with failure

### Implementation Notes

- **Layer:** Standalone script (scripts/)
- **Pattern reference:** Existing `scripts/ingest_products.py` structure
- **Key decisions:**
  - Cohere embed-multilingual-v3.0 (1024 dimensions)
  - Upsert on name + brand (unique constraint)
  - Retry with exponential backoff (max 3 retries)
  - Batch sizes: 100 for embedding, 50 for insert
- **Libraries:** cohere (for embeddings), supabase (for database)

### Scope Boundaries

- Do NOT modify database schema — separate feature (Step 1)
- Do NOT create API endpoints — separate feature (Step 3)
- Do NOT implement bot code — separate features (Steps 4-5)

### Files Expected

**New files:**
- `scripts/ingest_products.py` (replace existing OpenAI version with Cohere)
- `tests/test_ingest_products.py` (integration tests)
- `tests/test_product_generator.py` (unit tests)
- `tests/test_embedding_generator.py` (unit tests)

**Modified files:**
- None

**Must NOT modify:**
- None

### TDD Sequence

1. Test product generation (unit) — generate_products function
2. Test embedding generation (unit) — generate_embeddings function  
3. Test database insertion (integration) — insert_products function
4. Test error handling (unit + integration) — retry logic, partial failures