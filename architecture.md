# OpenClaw Architecture

```mermaid
graph TB
    User(["👤 User"])
    TG["Telegram Servers\n(api.telegram.org)"]

    subgraph Render_TBot["Render — Telegram Bot\ntelegram-bot-5340.onrender.com"]
        TBotApp["FastAPI App\n(run_bot.py → run_webhook)"]
        TBotHandlers["Handlers\n/start  /help  /scrape  messages"]
        TBotRL["Rate Limiter\n10 req/min per user"]
        TBotRetry["Retry Logic\nexp. backoff × 3"]
        TBotCH["ChatHandler"]
        TBotSS["SearchService"]
    end

    subgraph Render_API["Render — Backend API\nchatbot-bny4.onrender.com"]
        APIApp["FastAPI App\n(src/main.py)"]
        APIRL["Rate Limiter\n100 req/min"]
        APICH["ChatHandler"]
        APISS["SearchService"]
        APIScraper["Scraper\n(BeautifulSoup4)"]
        APIWhatsApp["WhatsApp Webhook\n/whatsapp/*\n(not active)"]
    end

    subgraph Supabase["Supabase (fddjpfipzonmfrzwpooj)"]
        PG["PostgreSQL"]
        PGVector["pgvector extension\nHNSW index\n1536-dim embeddings"]
        RLS["Row Level Security"]
    end

    Cohere["☁️ Cohere API\nembed-english-v3.0"]
    EcomSites["🌐 E-commerce Sites\n(outopia.com etc.)"]

    %% Telegram flow
    User -->|"sends message"| TG
    TG -->|"POST /webhook"| TBotApp
    TBotApp --> TBotHandlers
    TBotHandlers --> TBotRL
    TBotRL --> TBotRetry
    TBotRetry --> TBotCH
    TBotCH --> TBotSS

    %% Bot → scrape command calls backend API
    TBotHandlers -->|"/scrape cmd\nPOST /api/scrape"| APIApp

    %% Bot search path
    TBotSS -->|"generate query embedding"| Cohere
    TBotSS -->|"pgvector similarity search"| PGVector

    %% Bot replies
    TBotApp -->|"reply message"| TG
    TG -->|"delivers message"| User

    %% Backend API
    APIApp --> APIRL
    APIRL --> APICH
    APICH --> APISS
    APISS -->|"generate embedding"| Cohere
    APISS -->|"vector search"| PGVector
    APIApp --> APIScraper
    APIScraper -->|"HTTP scrape"| EcomSites
    APIScraper -->|"upsert products + embeddings"| PGVector

    %% Supabase internals
    PGVector --- PG
    RLS --- PG
```

## Services

| Service | URL | Runtime | Purpose |
|---------|-----|---------|---------|
| Telegram Bot | `telegram-bot-5340.onrender.com` | Render Web Service | Webhook receiver + search logic |
| Backend API | `chatbot-bny4.onrender.com` | Render Web Service | REST API + scraper |
| Database | `fddjpfipzonmfrzwpooj.supabase.co` | Supabase | pgvector product search |
| Embeddings | Cohere API | External | `embed-english-v3.0` |

## Request Flow — User Search

```
User msg → Telegram → POST /webhook (telegram-bot-5340)
  → RateLimit check (10/min)
  → ChatHandler → SearchService
      → parse NLP filters (price/category/gender via regex)
      → Cohere: generate 1536-dim query embedding
      → Supabase pgvector: cosine similarity search
  → format results (Markdown)
→ Telegram → User
```

## Request Flow — /scrape Command

```
/scrape <url> → telegram-bot-5340
  → POST chatbot-bny4.onrender.com/api/scrape
      → BeautifulSoup scrape target URL
      → generate embeddings per product (Cohere)
      → upsert into Supabase products table
  → reply "N products scraped"
```

## Notes

- Telegram bot runs in **webhook mode** (not polling) on Render
- Both services share same Supabase DB + Cohere key (independent connections)
- WhatsApp support coded but **not deployed/active** (placeholder keys in .env)
- OpenAI key is placeholder — only Cohere used for embeddings
