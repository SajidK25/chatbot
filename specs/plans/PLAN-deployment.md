# Plan: Deployment (Railway)

> **Date:** 2026-04-16
> **Project source:** PLAN-chatbot.md, Step 7
> **Estimated tasks:** 1
> **Planning session:** brief

## Summary

Deploy the OpenClaw chatbot to Railway with all required environment variables, configure Telegram and WhatsApp webhooks, and verify production operation.

## Requirements

### Functional Requirements
1. Deploy FastAPI backend to Railway
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

### 1. Railway Setup
- Install Railway CLI: `npm install -g @railway/cli`
- Login: `railway login`
- Initialize: `railway init`
- Select "Empty Project" or connect to GitHub

### 2. Set Environment Variables
```bash
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_ANON_KEY=...
railway variables set SUPABASE_SERVICE_KEY=...
railway variables set COHERE_API_KEY=...
railway variables set TELEGRAM_BOT_TOKEN=...
railway variables set WHATSAPP_TOKEN=...
railway variables set WHATSAPP_PHONE_NUMBER_ID=...
railway variables set WHATSAPP_VERIFY_TOKEN=...
railway variables set WHATSAPP_APP_SECRET=...
```

### 3. Deploy
```bash
railway up
```

### 4. Configure Telegram Webhook
Set Telegram bot webhook to: `https://your-railway-app.railway.app/whatsapp/webhook`
(Note: Telegram doesn't use this - it uses long polling by default)

### 5. Configure WhatsApp Webhook
In Meta Developer Portal:
- Callback URL: `https://your-railway-app.railway.app/whatsapp/webhook`
- Verify token: Set in WHATSAPP_VERIFY_TOKEN

### 6. Verify
- Health check: `curl https://your-railway-app.railway.app/health`
- Test search: `curl -X POST https://your-railway-app.railway.app/api/search -H "Content-Type: application/json" -d '{"query": "shoes"}'`

## Key Constraints

| Constraint | Why It Matters |
|------------|----------------|
| Railway uses port from PORT env var | Must set PORT=8000 |
| Telegram bot uses long polling | No webhook needed for Telegram |
| WhatsApp requires HTTPS | Railway provides HTTPS automatically |

## Scope Boundaries

### In Scope
- Deploy to Railway
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

## Open Questions (if any)

- None — this is a manual deployment step

---
_This plan is the input for the generate-tasks skill._
_Review this document, then run: "Generate task from plan: specs/plans/PLAN-deployment.md""