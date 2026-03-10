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

    # Create bot
    app = create_bot()

    # Setup scheduler
    scheduler = setup_scheduler(app.bot)

    async def post_init(application) -> None:
        scheduler.start()
        logger.info(f"Scheduler started, polling every {settings.poll_interval_minutes} minutes")

    async def post_shutdown(application) -> None:
        scheduler.shutdown()

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    logger.info("FeedPulse starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
