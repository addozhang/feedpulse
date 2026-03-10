import asyncio
import logging

from feedpulse.config import settings
from feedpulse.db import init_db
from feedpulse.bot import create_bot
from feedpulse.scheduler import setup_scheduler


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    if not settings.telegram_bot_token:
        logger.error("FEEDPULSE_TELEGRAM_BOT_TOKEN is required")
        raise SystemExit(1)

    # Init DB
    asyncio.run(init_db())

    if settings.api_enabled:
        asyncio.run(_run_with_api(logger))
    else:
        _run_bot_only(logger)


def _run_bot_only(logger: logging.Logger) -> None:
    """Original flow: run the Telegram bot with run_polling()."""
    app = create_bot()
    scheduler = setup_scheduler(app.bot)

    async def post_init(application) -> None:
        from feedpulse.i18n import get_messages
        msg = get_messages(settings.language)
        await application.bot.set_my_commands([
            ("start", msg["cmd_start"]),
            ("add", msg["cmd_add"]),
            ("list", msg["cmd_list"]),
            ("remove", msg["cmd_remove"]),
            ("check", msg["cmd_check"]),
        ])
        scheduler.start()
        logger.info(f"Scheduler started, polling every {settings.poll_interval_minutes} minutes")

    async def post_shutdown(application) -> None:
        scheduler.shutdown()

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    logger.info("FeedPulse starting...")
    app.run_polling()


async def _run_with_api(logger: logging.Logger) -> None:
    """Run both the Telegram bot and FastAPI server concurrently."""
    import uvicorn
    from feedpulse.api import app as fastapi_app
    from feedpulse.i18n import get_messages

    # --- Telegram bot setup (low-level async API) ---
    bot_app = create_bot()
    scheduler = setup_scheduler(bot_app.bot)

    await bot_app.initialize()
    msg = get_messages(settings.language)
    await bot_app.bot.set_my_commands([
        ("start", msg["cmd_start"]),
        ("add", msg["cmd_add"]),
        ("list", msg["cmd_list"]),
        ("remove", msg["cmd_remove"]),
        ("check", msg["cmd_check"]),
    ])
    await bot_app.start()
    await bot_app.updater.start_polling()
    scheduler.start()
    logger.info(f"Scheduler started, polling every {settings.poll_interval_minutes} minutes")

    # --- Uvicorn setup ---
    uvicorn_config = uvicorn.Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(uvicorn_config)

    logger.info(f"FeedPulse starting (API on port {settings.api_port})...")

    # Uvicorn handles SIGINT/SIGTERM internally via capture_signals().
    # When it exits, we clean up the bot and scheduler.
    try:
        await server.serve()
    finally:
        logger.info("Shutting down bot and scheduler...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        scheduler.shutdown()
        logger.info("FeedPulse stopped.")


if __name__ == "__main__":
    main()
