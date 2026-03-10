import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from feedpulse.config import settings
from feedpulse.db import get_db
from feedpulse.fetcher import check_all_feeds

logger = logging.getLogger(__name__)


async def notify_subscribers(bot: Bot) -> int:
    """Check all feeds and notify subscribers of new entries. Returns total sent."""
    updates = await check_all_feeds()
    if not updates:
        return 0

    db = await get_db()
    total = 0
    try:
        for feed_id, entries in updates.items():
            # Get feed info
            cursor = await db.execute("SELECT title, url FROM feeds WHERE id = ?", (feed_id,))
            feed = await cursor.fetchone()
            feed_title = feed["title"] or feed["url"]

            # Get subscribers
            cursor = await db.execute(
                "SELECT chat_id FROM subscriptions WHERE feed_id = ?", (feed_id,)
            )
            subs = await cursor.fetchall()

            for entry in entries:
                title = entry["title"]
                link = entry["link"]
                text = f"📰 <b>{feed_title}</b>\n\n<b>{title}</b>\n{link}"

                for sub in subs:
                    try:
                        await bot.send_message(
                            chat_id=sub["chat_id"],
                            text=text,
                            parse_mode="HTML",
                            disable_web_page_preview=False,
                        )
                        total += 1
                    except Exception as e:
                        logger.error(f"Failed to send to {sub['chat_id']}: {e}")
    finally:
        await db.close()

    logger.info(f"Notified {total} messages across feeds")
    return total


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notify_subscribers,
        "interval",
        minutes=settings.poll_interval_minutes,
        args=[bot],
        id="feed_checker",
        name="Feed Update Checker",
    )
    return scheduler
