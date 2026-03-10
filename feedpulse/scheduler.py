import html
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from feedpulse.config import settings
from feedpulse.db import get_db
from feedpulse.fetcher import check_all_feeds

logger = logging.getLogger(__name__)

MAX_MSG_LEN = 4000  # Telegram limit is 4096, leave margin


def _build_message(feed_title: str, entry: dict) -> str:
    """Build HTML message with proper escaping and length limit."""
    safe_feed = html.escape(feed_title)
    safe_title = html.escape(entry["title"])
    link = entry["link"]
    text = f"📰 <b>{safe_feed}</b>\n\n<b>{safe_title}</b>\n{link}"
    if len(text) > MAX_MSG_LEN:
        text = text[:MAX_MSG_LEN] + "…"
    return text


async def notify_subscribers(
    bot: Bot,
    chat_id: int | None = None,
) -> int:
    """Check feeds and notify subscribers. If chat_id given, only check that chat's feeds."""
    updates = await check_all_feeds(chat_id=chat_id)
    if not updates:
        return 0

    total = 0
    async with get_db() as db:
        for feed_id, entries in updates.items():
            cursor = await db.execute(
                "SELECT title, url FROM feeds WHERE id = ?", (feed_id,)
            )
            feed = await cursor.fetchone()
            feed_title = feed["title"] or feed["url"]

            cursor = await db.execute(
                "SELECT chat_id FROM subscriptions WHERE feed_id = ?", (feed_id,)
            )
            subs = await cursor.fetchall()

            for entry in entries:
                text = _build_message(feed_title, entry)
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
