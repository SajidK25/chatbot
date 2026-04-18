# Plan: Product Scraping & CLI Tool

> **Date:** 2026-04-18
> **Project source:** Standalone (extension to existing chatbot)
> **Estimated tasks:** 4-5 tasks
> **Planning session:** brief

## Summary

Extend existing Telegram chatbot with product scraping capability. Add CLI tool for scraping outopia.com products and importing/exporting product data in OpenAI commerce spec format. Products stored in existing Supabase `products` table, extended with SKU, sizes, colors, and separate Cohere embedding column.

## Requirements

### Functional Requirements
1. User executes `/scrape <URL>` command in Telegram to trigger scraping
2. CLI tool scrapes outopia.com product pages (men/women collections)
3. Scraped products saved to Supabase (update if exists)
4. CLI tool exports products in OpenAI commerce spec JSON format
5. CLI tool imports products from OpenAI commerce spec JSON file

### Non-Functional Requirements
1. 2-second delay between HTTP requests to avoid rate limiting
2. Handle 429 responses with backoff retry
3. Telegram rate limit: 10 messages/min per user
4. Embedding dimension: 1024 (Cohere embed-multilingual-v3.0)

## Behaviors

**Scrape Command**
- `/scrape https://outopia.com/collections/men` - scrape specific collection URL
- Parse product fields: name, price, description, images, SKU, sizes, colors
- Update existing product if SKU matches, insert new if not found

**Duplicate Handling**
- Match by SKU field
- Update all fields on match (name, price, description, images, sizes, colors)

**Export/Import**
- Export all products to JSON in OpenAI commerce spec format
- Import from JSON file following same spec

**Why rules matter:**
- SKU matching ensures product updates don't create duplicates
- Rate limiting prevents IP ban from outopia.com
- OpenAI spec enables ChatGPT product discovery

**Common mistakes:**
- Creating duplicate products instead of updating
- Not handling 429 rate limit responses
- Using wrong embedding dimension (1536 vs 1024)

## Detailed Specifications

### Database Schema Extension

**New columns in products table:**
| Field | Type | Constraints |
|-------|------|-------------|
| sku | TEXT | UNIQUE, NOT NULL |
| sizes | JSONB | DEFAULT '[]'::jsonb |
| colors | JSONB | DEFAULT '[]'::jsonb |
| cohere_embedding | vector(1024) | NULL |

**Index:**
```sql
CREATE INDEX IF NOT EXISTS products_sku_idx ON products(sku);
CREATE INDEX IF NOT EXISTS products_cohere_embedding_idx ON products 
USING hnsw (cohere_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Scraper Service

**Purpose:** Scrape product data from e-commerce sites

**Interface:**
```python
async def scrape_products(url: str) -> list[ScrapedProduct]
```

**Behavior:**
- Fetch HTML from URL
- Parse product cards: name, price, description, images, SKU, sizes, colors
- Handle pagination if present
- Add 2-second delay between requests
- Retry 429 with exponential backoff (3 retries)

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Site unreachable | Show error "Failed to fetch URL. Check URL and try again." |
| 429 response | Wait 30s, retry up to 3 times |
| Invalid URL format | Show error "Invalid URL. Use format: https://..." |
| Parsing failed | Show error "Failed to parse products. Site may have changed." |

### CLI Tool

**Purpose:** Command-line interface for scraping and import/export

**Commands:**
```
openclaw scrape <URL>          # Scrape products from URL
openclaw export <file.json>   # Export products to JSON
openclaw import <file.json>   # Import products from JSON
```

**Export Format (OpenAI commerce spec):**
```json
{
  "header": {
    "feed_id": "openclaw_feed",
    "account_id": "openclaw",
    "target_merchant": "outopia",
    "target_country": "US"
  },
  "products": [
    {
      "id": "SKU12345",
      "title": "Product Name",
      "description": { "plain": "Description" },
      "url": "https://...",
      "media": [...],
      "variants": [...]
    }
  ]
}
```

**Import Behavior:**
- Parse JSON file
- Validate against OpenAI spec
- Insert/update products in database
- Report summary: X inserted, Y updated, Z failed

### Telegram Command

**Purpose:** User trigger for scraping

**Interface:**
- Command: `/scrape <URL>`
- Example: `/scrape https://outopia.com/collections/men`

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| No URL provided | Reply "Usage: /scrape <URL>" |
| Invalid URL | Reply "Invalid URL format" |
| Scrape failed | Reply with error message |
| Scrape success | Reply "Scraped X products. Y new, Z updated." |

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| SKU as unique key | Prevents duplicate products |
| 1024 embedding dimension | Cohere embed-multilingual-v3.0 uses 1024 |
| 2-second request delay | Avoids rate limiting from outopia.com |
| Separate process from bot | CLI runs outside Telegram context |

## Edge Cases & Failure Modes

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Product with no SKU | Generate SKU from name+price hash | SKU required for matching |
| Outopia blocks requests | Retry 3x with 30s backoff, then error | Graceful degradation |
| Empty product page | Report "No products found" | Clear user feedback |
| Duplicate SKU conflict | Update existing, skip new | Preserve product ID/history |
| Invalid JSON import | Report validation errors, skip invalid | Data integrity |

## Decisions Log

| # | Decision | Alternatives Considered | Chosen Because |
|---|----------|------------------------|----------------|
| 1 | Use SKU as unique key | Use product URL or generate ID | SKU stable across updates |
| 2 | CLI tool separate from bot | Integrate in bot | CLI runs independently |
| 3 | New embedding column | Replace old 1536 dimension | Maintain backward compatibility |
| 4 | Update on duplicate | Skip or reject | Product updates preferred |

## Scope Boundaries

### In Scope
- Database schema extension (sku, sizes, colors, cohere_embedding)
- Scraper service for outopia.com
- CLI tool (scrape, export, import commands)
- Telegram /scrape command

### Out of Scope
- WhatsApp bot (Telegram only for this extension)
- Scheduled/automated scraping (manual trigger only)
- Other e-commerce sites (outopia.com only)

## Dependencies

### Depends On (must exist before this work starts)
- Existing `products` table in Supabase
- Existing Telegram bot infrastructure
- Cohere API key configured

### Depended On By (other work waiting for this)
- None currently

## Architecture Notes

- Scraper service separate from bot (runs in CLI process)
- Telegram command just triggers background scrape job
- Results stored in Supabase, bot queries for display
- Export/import handles OpenAI commerce spec JSON

## Open Questions

- None - all resolved in planning session

---

# Tasks

## Task T1: Database Schema Extension

> **Status:** done
> **Effort:** xs
> **Priority:** critical
> **Depends on:** None

### Description

Add new columns (sku, sizes, colors, cohere_embedding) to existing products table in Supabase. Create migration script in src/database/migrations/. Create HNSW index for vector search on cohere_embedding column.

### Test Plan

#### Test File(s)
- `tests/test_schema_migration.py` (new file)

#### Test Scenarios

##### Schema Migration

- **adds sku column** — GIVEN migration script WHEN executed THEN products table has sku column with UNIQUE constraint
- **adds sizes column** — GIVEN migration script WHEN executed THEN products table has sizes column with JSONB type
- **adds colors column** — GIVEN migration script WHEN executed THEN products table has colors column with JSONB type
- **adds cohere_embedding column** — GIVEN migration script WHEN executed THEN products table has cohere_embedding column with vector(1024) type
- **creates sku index** — GIVEN migration script WHEN executed THEN products_sku_idx exists
- **creates cohere embedding index** — GIVEN migration script WHEN executed THEN products_cohere_embedding_idx exists with hnsw

### Implementation Notes

- **Layer(s):** Database
- **Pattern reference:** src/database/schema.sql
- **Key decisions:** SKU as unique key, 1024 embedding dimension
- **Libraries:** psycopg2-binary

### Scope Boundaries

- Do NOT modify existing columns
- Do NOT drop existing data
- Only add new columns and indexes

### Files Expected

**New files:**
- `src/database/migrations/001_add_product_fields.sql`

**Modified files:**
- None

### TDD Sequence

1. Write test for column existence
2. Write migration SQL
3. Verify migration runs successfully

## Task T2: Scraper Service

> **Status:** done
> **Effort:** m
> **Priority:** high
> **Depends on:** T1

### Description

Build scraper service that fetches product pages from outopia.com and parses product data (name, price, description, images, SKU, sizes, colors). Include rate limiting (2-second delay) and retry logic for 429 responses.

### Test Plan

#### Test File(s)
- `tests/test_scraper.py` (new file)

#### Test Scenarios

##### HTML Parsing

- **parses product name** — GIVEN HTML with product card WHEN parsed THEN product name extracted
- **parses product price** — GIVEN HTML with product card WHEN parsed THEN product price extracted
- **parses product description** — GIVEN HTML with product card WHEN parsed THEN product description extracted
- **parses product images** — GIVEN HTML with product card WHEN parsed THEN image URLs extracted
- **parses product SKU** — GIVEN HTML with product card WHEN parsed THEN SKU extracted
- **parses product sizes** — GIVEN HTML with product card WHEN parsed THEN sizes array extracted
- **parses product colors** — GIVEN HTML with product card WHEN parsed THEN colors array extracted

##### Rate Limiting

- **adds delay between requests** — GIVEN multiple URLs WHEN scraped THEN 2-second delay between requests
- **respects rate limit** — GIVEN 100 URLs WHEN scraped THEN total time >= 200 seconds

##### Error Handling

- **handles 429 response** — GIVEN 429 response WHEN scraping THEN retry after 30s, up to 3 times
- **handles timeout** — GIVEN connection timeout WHEN scraping THEN raise timeout error
- **handles invalid URL** — GIVEN invalid URL WHEN scraping THEN raise invalid URL error
- **handles empty page** — GIVEN empty HTML response WHEN parsed THEN return empty list

### Implementation Notes

- **Layer(s):** Service
- **Pattern reference:** src/services/search_service.py
- **Key decisions:** 2-second delay, 3 retries with 30s backoff
- **Libraries:** httpx, beautifulsoup4

### Scope Boundaries

- Do NOT save to database (T3 handles)
- Do NOT handle pagination (outopia.com doesn't use)
- Only parse outopia.com HTML structure

### Files Expected

**New files:**
- `src/services/scraper.py`
- `tests/test_scraper.py`

**Modified files:**
- `requirements.txt` (add beautifulsoup4)

### TDD Sequence

1. Write tests for HTML parsing (mock HTML)
2. Write scraper function
3. Add rate limiting
4. Add retry logic

## Task T3: CLI Tool

> **Status:** done
> **Effort:** m
> **Priority:** high
> **Depends on:** T2

### Description

Build CLI tool with three commands: scrape (triggers scraping), export (products to JSON), import (JSON to products). Use Click framework. Save products to Supabase with SKU matching for updates.

### Test Plan

#### Test File(s)
- `tests/test_cli.py` (new file)

#### Test Scenarios

##### Scrape Command

- **accepts URL argument** — GIVEN URL WHEN openclaw scrape runs THEN products saved to database
- **shows progress** — GIVEN scrape command WHEN running THEN progress displayed
- **reports summary** — GIVEN successful scrape THEN report X products scraped

##### Export Command

- **exports to file** — GIVEN products in database WHEN openclaw export runs THEN JSON file created
- **follows OpenAI spec** — GIVEN export WHEN running THEN JSON matches OpenAI commerce spec format

##### Import Command

- **imports from file** — GIVEN valid JSON file WHEN openclaw import runs THEN products saved to database
- **updates existing products** — GIVEN product with existing SKU WHEN imported THEN product updated
- **inserts new products** — GIVEN product with new SKU WHEN imported THEN product inserted

##### Validation

- **rejects invalid JSON** — GIVEN invalid JSON file WHEN imported THEN error reported
- **reports import summary** — GIVEN import THEN report X inserted, Y updated, Z failed

### Implementation Notes

- **Layer(s):** CLI
- **Pattern reference:** Click framework (similar to existing scripts)
- **Key decisions:** SKU matching for updates
- **Libraries:** Click

### Scope Boundaries

- Do NOT embed directly in bot (T4 handles)
- Do NOT verify scraped data (outopia.com trusted)
- Only OpenAI commerce spec format

### Files Expected

**New files:**
- `src/cli.py`
- `tests/test_cli.py`

**Modified files:**
- `requirements.txt` (add click)

### TDD Sequence

1. Write export tests
2. Write import tests
3. Write scrape command tests
4. Implement CLI

## Task T4: Telegram /scrape Command

> **Status:** done
> **Effort:** s
> **Priority:** medium
> **Depends on:** T3

### Description

Add /scrape command to Telegram bot. Parse URL from command arguments. Trigger scraping via CLI subprocess or direct call. Return status message to user.

### Test Plan

#### Test File(s)
- `tests/test_telegram_scrape.py` (new file)

#### Test Scenarios

##### Command Handling

- **parses URL from argument** — GIVEN "/scrape https://outopia.com/collections/men" WHEN command received THEN URL extracted
- **shows usage without URL** — GIVEN "/scrape" WHEN command received THEN "Usage: /scrape <URL>" returned
- **validates URL format** — GIVEN "/scrape not-a-url" WHEN command received THEN "Invalid URL format" returned

##### Scraping Integration

- **runs scrape successfully** — GIVEN "/scrape https://outopia.com/collections/men" WHEN scrape succeeds THEN "Scraped X products" message returned
- **handles scrape failure** — GIVEN "/scrape https://outopia.com/collections/men" WHEN scrape fails THEN error message returned

### Implementation Notes

- **Layer(s):** Bot
- **Pattern reference:** src/bots/telegram_bot.py
- **Key decisions:** Separate process for scraping
- **Libraries:** python-telegram-bot

### Scope Boundaries

- Do NOT implement scraping logic (T2/T3)
- Do NOT add WhatsApp command
- Only single URL per command

### Files Expected

**New files:**
- None (modify existing telegram_bot.py)

**Modified files:**
- `src/bots/telegram_bot.py`
- `tests/test_telegram_bot.py` (add tests)

### TDD Sequence

1. Write command parsing tests
2. Add command handler to bot
3. Test integration