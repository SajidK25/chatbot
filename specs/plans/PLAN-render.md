# Plan: Deployment (Render)

> **Date:** 2026-04-16
> **Project source:** PLAN-chatbot.md, Step 7 (Alternative)
> **Estimated tasks:** 1
> **Planning session:** brief

## Summary

Deploy the OpenClaw chatbot to Render with all required environment variables, configure Telegram and WhatsApp webhooks, and verify production operation.

## Requirements

### Functional Requirements
1. Deploy FastAPI backend to Render
2. Set all required environment variables
3. Configure Telegram bot webhook
4. Configure WhatsApp webhook
5. Verify production operation

### Environment Variables Required
| Variable | Description | Required |
|----------|-------------|----------|
| SUPABASE_URL | Supabase project URL | Yes |
| SUPABASE_ANON_KEY | Supabase anon key | Yes |
| SUPABASE_SERVICE_KEY | Supabase service role key | Yes |
| COHERE_API_KEY | Cohere API key for embeddings | Yes |
| TELEGRAM_BOT_TOKEN | Telegram bot token | Yes |
| WHATSAPP_TOKEN | WhatsApp access token | No |
| WHATSAPP_PHONE_NUMBER_ID | WhatsApp phone number ID | No |
| WHATSAPP_VERIFY_TOKEN | WhatsApp webhook verify token | No |
| WHATSAPP_APP_SECRET | WhatsApp app secret | No |
| PORT | Server port (8000) | No |
| DEBUG | Debug mode (false) | No |

## Deployment Steps

### 1. Render Setup
- Sign up at render.com
- Connect your GitHub repository
- Create a new "Web Service"

### 2. Configure Build Settings
| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` |
| Runtime | Python 3.11 |

### 3. Set Environment Variables
In Render dashboard, add the following environment variables:
```
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
COHERE_API_KEY=...
TELEGRAM_BOT_TOKEN=...
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
WHATSAPP_APP_SECRET=...
PORT=8000
```

### 4. Deploy
- Click "Deploy" in Render dashboard
- Wait for build and deployment to complete

### 5. Configure Telegram Webhook
Telegram uses long polling by default, so no webhook needed for the bot.

### 6. Configure WhatsApp Webhook
In Meta Developer Portal:
- Callback URL: `https://your-render-app.onrender.com/whatsapp/webhook`
- Verify token: Set in WHATSAPP_VERIFY_TOKEN

### 7. Verify
- Health check: `curl https://your-render-app.onrender.com/health`
- Test search: `curl -X POST https://your-render-app.onrender.com/api/search -H "Content-Type: application/json" -d '{"query": "shoes"}'`

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| Render requires runtime.txt | Must specify Python version |
| Telegram uses long polling | No webhook needed |
| WhatsApp requires HTTPS | Render provides HTTPS automatically |
| PORT env var in start command | Render uses $PORT variable |

## Files Required for Render

### runtime.txt
```
python-3.11
```

### (Optional) Procfile
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
```
Note: Render can use start command directly, Procfile is optional.

## Scope Boundaries

### In Scope
- Deploy to Render
- Set environment variables
- Configure WhatsApp webhook
- Verify deployment

### Out of Scope
- Creating Supabase project (Step 1)
- Ingesting product data (Step 2)

## Dependencies

### Depends On (must exist before this work starts)
- Steps 1-6 complete
- Supabase project with data
- Telegram bot created via @BotFather
- WhatsApp Business Cloud API setup

## Comparison: Railway vs Render

| Feature | Railway | Render |
|---------|---------|--------|
| Free tier | Yes (limited) | Yes (limited) |
| Auto-deploy | Yes | Yes |
| HTTPS | Automatic | Automatic |
| Environment variables | Via CLI | Via dashboard |
| Start command | Flexible | Via dashboard |

## Open Questions (if any)

- None — this is a manual deployment step

---
_This plan is the input for the generate-tasks skill._
_Review this document, then run: "Generate task from plan: specs/plans/PLAN-render.md""