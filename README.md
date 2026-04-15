# OpenClaw Chatbot

AI-powered e-commerce chatbot for Telegram and WhatsApp with semantic product search.

## Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Setup Supabase**
- Create project at supabase.com
- Run `src/database/schema.sql` in SQL Editor
- Get your URL and keys

4. **Ingest products**
```bash
python scripts/ingest_products.py
```

5. **Run the API**
```bash
uvicorn src.main:app --reload
```

6. **Run Telegram bot** (in separate terminal)
```bash
python -m src.bots.telegram_bot
```

## Configuration

See `.env.example` for required environment variables.

## Demo Products

The ingestion script generates 500 realistic products across:
- Fashion (shoes, clothing, accessories)
- Electronics (headphones, speakers, gadgets)
- Home (furniture, decor, organization)
- Beauty (skincare, haircare, cosmetics)

Each product has semantic embeddings for intelligent search.

## Testing

```bash
python scripts/test_queries.py
```

## Deployment

Deploy to Railway/Render with the required environment variables.