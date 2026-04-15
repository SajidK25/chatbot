# Plan: Supabase Setup

> **Date:** 2026-04-15
> **Project source:** PLAN-chatbot.md, Step 1
> **Estimated tasks:** 5-7
> **Planning session:** detailed

## Summary

Setting up Supabase as the database backend for the OpenClaw chatbot. This includes creating a new Supabase project, enabling pgvector extension, creating the products table with vector column for semantic search, and configuring RLS policies. This is the foundational infrastructure layer that all subsequent features depend on.

## Requirements

### Functional Requirements
1. Create new Supabase project
2. Enable pgvector extension
3. Create products table with vector(1024) column for embeddings
4. Create HNSW index on embedding column for similarity search
5. Create standard indexes on filter columns (category, price, gender)
6. Enable Row Level Security (RLS)
7. Create RLS policies for authenticated users (read + write)
8. Obtain and document API credentials (URL, anon key, service key)

### Non-Functional Requirements
1. Database region: any (free tier)
2. Embedding model: Cohere embed-multilingual-v3.0 (1024 dimensions, free tier)
3. RLS must not block the data ingestion script (uses service key)

## Behaviors

### Database Schema

**Why it matters:**
- The vector column stores product embeddings for semantic search — the core capability of the chatbot
- 1024 dimensions matches Cohere's embed-multilingual-v3.0 output
- HNSW index enables fast cosine similarity searches at scale

**What's optional vs required:**
- Products table is required now; users/conversations tables deferred to future
- Standard indexes on category, price, gender are required for filtered queries

**Common mistakes:**
- Using wrong vector dimension (1536 vs 1024) causes embedding insertion failures
- Forgetting to create HNSW index results in slow searches
- Overly restrictive RLS blocks data ingestion

## Detailed Specifications

### Supabase Project

**Purpose:** Host PostgreSQL database with pgvector extension for vector similarity search

**Behavior:**
- Create new project via supabase.com dashboard
- Select any available region (free tier)
- Enable pgvector extension immediately after project creation

### pgvector Extension

**Purpose:** Enable vector operations and data type

**Behavior:**
- Run: `CREATE EXTENSION IF NOT EXISTS vector;`
- This is a one-time setup per database

### Products Table

**Purpose:** Store product catalog with vector embeddings for semantic search

**Interface:**
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category TEXT NOT NULL,
    image_url TEXT NOT NULL,
    product_url TEXT NOT NULL,
    brand TEXT NOT NULL,
    gender TEXT,
    embedding vector(1024),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Validation Rules:**
- id: UUID, auto-generated
- name: TEXT, NOT NULL
- description: TEXT, NOT NULL
- price: DECIMAL(10,2), NOT NULL, positive values only
- category: TEXT, NOT NULL (Fashion, Electronics, Home, Beauty)
- image_url: TEXT, NOT NULL, valid URL format
- product_url: TEXT, NOT NULL, valid URL format
- brand: TEXT, NOT NULL
- gender: TEXT, nullable (men, women, unisex)
- embedding: vector(1024), nullable (populated during ingestion)
- created_at: TIMESTAMPTZ, auto-generated

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Insert with invalid vector dimension | Error: vector dimension mismatch |
| Insert with NULL required field | Error: null value violates not null constraint |
| Negative price value | Error: constraint violation (should add CHECK) |

### HNSW Index

**Purpose:** Enable fast cosine similarity search on embeddings

**Interface:**
```sql
CREATE INDEX products_embedding_idx ON products 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Behavior:**
- Uses HNSW algorithm for approximate nearest neighbor search
- m=16: number of connections per layer
- ef_construction=64: search width during index build

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Index creation on table with existing data | Successfully builds index, may take time |
| Vector column doesn't exist | Error: cannot create index |

### Standard Indexes

**Purpose:** Speed up filtered queries on metadata columns

**Interface:**
```sql
CREATE INDEX products_category_idx ON products(category);
CREATE INDEX products_price_idx ON products(price);
CREATE INDEX products_gender_idx ON products(gender);
```

### Row Level Security (RLS)

**Purpose:** Control access to products table based on authentication status

**Interface:**
```sql
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Policy for authenticated users (read + write)
CREATE POLICY "products_authenticated_select" ON products
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "products_authenticated_insert" ON products
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "products_authenticated_update" ON products
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Policy for service role (bypasses RLS, for data ingestion)
CREATE POLICY "products_service_all" ON products
    FOR ALL USING (auth.role() = 'service_role');
```

**Behavior:**
- Authenticated users can SELECT, INSERT, UPDATE
- Service role key bypasses RLS entirely
- Anonymous users cannot access

**Error Scenarios:**
| Condition | Expected Behavior |
|-----------|-------------------|
| Anonymous user attempts SELECT | Error: row-level security policy violation |
| Authenticated user attempts DELETE | Error: no policy allows DELETE |

### API Credentials

**Purpose:** Provide connection details for application code

**Behavior:**
- SUPABASE_URL: Project URL from dashboard
- SUPABASE_ANON_KEY: Public anon key for client access
- SUPABASE_SERVICE_KEY: Secret service key for admin operations (data ingestion)

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| Vector dimension must be 1024 | Matches Cohere embed-multilingual-v3.0 output; 1536 causes insertion failures |
| Service key must stay secret | Bypasses RLS; exposed key allows unauthorized data access |
| HNSW index required | Without it, vector search is too slow for production use |
| RLS must allow service role | Data ingestion script needs to insert products |

## Edge Cases & Failure Modes

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Supabase region doesn't have pgvector | Verify region supports pgvector before selecting | Most regions support it, but worth checking |
| Insert embedding with wrong dimension | Reject with clear error message | Prevents corrupted data |
| All RLS policies accidentally deleted | Service role can still access; data not lost | Service key is backup access |
| Large dataset during index creation | HNSW builds async; may take minutes | Don't interrupt; index builds in background |

## Decisions Log

| # | Decision | Alternatives Considered | Chosen Because |
|---|----------|------------------------|----------------|
| 1 | Use Cohere embed-multilingual-v3.0 | Sentence Transformers (local), OpenAI (paid) | Free tier (1M tokens/month), similar API to OpenAI, easy swap |
| 2 | Vector dimension 1024 | 1536 (OpenAI default), 768 (smaller models) | Cohere outputs 1024 dimensions; matches model |
| 3 | RLS: authenticated users read+write | Public read-only, authenticated read-only | Allows future admin features; service role handles ingestion |
| 4 | HNSW m=16, ef_construction=64 | Default values vs tuned | Good balance of search quality and build time; pgvector defaults |
| 5 | Database region: any | Closest to users, specific region | Free tier limits options; any works for demo |

## Scope Boundaries

### In Scope
- Supabase project creation
- pgvector extension enablement
- Products table with schema
- HNSW index for vector search
- Standard indexes for filters
- RLS policies for authenticated + service role
- API credential documentation

### Out of Scope
- Other tables (users, conversations, orders) — deferred to future features
- Data ingestion script — separate feature (Step 2 in PLAN-chatbot.md)
- API endpoint code — separate feature (Step 3)

## Dependencies

### Depends On (must exist before this work starts)
- Supabase account (user has account)

### Depended On By (other work waiting for this)
- Data ingestion script (Step 2) — needs table + indexes + service key
- FastAPI backend (Step 3) — needs Supabase connection

## Architecture Notes

This is the foundational data layer. The schema uses UUID for product IDs (auto-generated), vector(1024) for embeddings, and standard columns for product metadata. RLS is enabled with policies that allow authenticated users full access while keeping service role as admin bypass. This matches the project architecture of a unified chatbot backend with Supabase as the data store.

## Open Questions (if any)

- None — all decisions resolved in this session

---
_This plan is the input for the generate-tasks skill._
_Review this document, then run: "Generate task from plan: specs/plans/PLAN-supabase-setup.md"_

---

# Tasks

## Task T1: Supabase Database Setup

> **Status:** not started
> **Effort:** s
> **Priority:** critical
> **Depends on:** None

### Description

Execute all SQL scripts to set up Supabase infrastructure: create products table with vector column, create indexes (HNSW + standard), enable RLS with policies, and document the API credentials. This is the foundational data layer for the OpenClaw chatbot.

### Test Plan

#### Test File(s)
- N/A — Infrastructure verification via SQL queries (documented in implementation)

#### Test Scenarios

##### Database Schema Verification

- **products table exists** — Query information_schema.tables returns products table
- **vector column has dimension 1024** — embedding column is vector(1024), not 1536
- **all required columns present** — id, name, description, price, category, image_url, product_url, brand, gender, embedding, created_at

##### Index Verification

- **HNSW index exists** — Index `products_embedding_idx` present on embedding column with vector_cosine_ops
- **standard indexes exist** — Indexes on category, price, gender columns

##### Security Verification

- **RLS enabled** — relrowsecurity = true on products table
- **RLS policies exist** — 4 policies present: products_authenticated_select, products_authenticated_insert, products_authenticated_update, products_service_all

### Implementation Notes

- **Layer:** Infrastructure (SQL)
- **Pattern reference:** SQL scripts in src/database/schema.sql (to be created)
- **Key decisions:**
  - Vector dimension 1024 (Cohere embed-multilingual-v3.0)
  - RLS: authenticated users read+write, service role bypass
  - HNSW index m=16, ef_construction=64
- **Libraries:** N/A — pure SQL executed in Supabase dashboard

### Scope Boundaries

- Do NOT create data ingestion script — separate feature (Step 2)
- Do NOT create FastAPI endpoints — separate feature (Step 3)
- Do NOT create other tables (users, conversations) — deferred to future

### Files Expected

**New files:**
- `src/database/schema.sql` — All SQL statements for table, indexes, RLS

**Modified files:**
- None

**Must NOT modify:**
- None

### Manual Steps Required

1. Create Supabase project at supabase.com
2. Run `CREATE EXTENSION IF NOT EXISTS vector;` in SQL editor
3. Run `src/database/schema.sql` in SQL editor
4. Document API credentials in .env file:
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - SUPABASE_SERVICE_KEY
5. Verify setup via SQL queries listed in test plan

### TDD Sequence

N/A — This is an infrastructure task executed manually in Supabase. TDD applies to code, not database setup.