#!/usr/bin/env python
"""Entry point for bot webhook mode"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("BOT_MODE", os.environ.get("BOT_MODE", "webhook"))
os.environ.setdefault("PORT", os.environ.get("PORT", "8000"))

if __name__ == "__main__":
    if os.environ.get("BOT_MODE") == "webhook":
        import uvicorn
        from src.bots.telegram_bot import run_webhook

        port = int(os.environ.get("PORT", "8000"))
        app = run_webhook()
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        from src.bots.telegram_bot import run_polling

        run_polling()
