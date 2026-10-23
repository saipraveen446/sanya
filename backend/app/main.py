"""FastAPI entry point: CORS, /api routes, health check, Telegram webhook/polling."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import Application

from app.api.routes import router
from app.config import settings
from app.database import init_db
from app.llm import llm_status
from app.skills.registry import load_skills
from app.skills.reminders.scheduler import run_alert_loop
from app.skills.reminders.notify import bind_bot

bot_app: Application | None = None
_use_webhook = bool(settings.public_url and settings.telegram_bot_token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app
    load_skills()
    await init_db()
    if settings.telegram_bot_token:
        from app.bot.telegram_bot import build_bot

        bot_app = build_bot()
        bind_bot(lambda: bot_app)
        await bot_app.initialize()
        await bot_app.start()
        if _use_webhook:
            webhook_url = f"{settings.public_url}/api/telegram/webhook"
            await bot_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        else:
            await bot_app.updater.start_polling(drop_pending_updates=True)
    alert_task = asyncio.create_task(run_alert_loop(lambda: bot_app))
    yield
    alert_task.cancel()
    if bot_app:
        if _use_webhook:
            await bot_app.bot.delete_webhook()
        else:
            await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


app = FastAPI(title="Sanya", description="Personal Assistant", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    if not bot_app:
        return Response(status_code=503)
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return Response(status_code=200)


@app.get("/api/health")
async def health():
    bot_name = None
    polling = False
    if bot_app and bot_app.bot:
        bot_name = bot_app.bot.username
        polling = bool(bot_app.updater and bot_app.updater.running) or _use_webhook
    llm = llm_status()
    return {
        "status": "ok",
        "telegram": bool(settings.telegram_bot_token),
        "telegram_bot": f"@{bot_name}" if bot_name else None,
        "telegram_polling": polling,
        "llm": llm["enabled"],
        "llm_provider": llm["provider"],
        "llm_model": llm["model"],
        "llm_order": llm["order"],
        "llm_available": llm["available"],
    }
