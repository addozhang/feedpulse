import logging
import sqlite3

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from feedpulse.config import settings
from feedpulse.db import get_db
from feedpulse.fetcher import fetch_feed, seed_feed_entries
from feedpulse.i18n import get_messages

logger = logging.getLogger(__name__)
msg = get_messages(settings.language)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(msg["help"])


async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text(msg["add_usage"])
        return

    url = ctx.args[0].strip()
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    reply = await update.message.reply_text(msg["validating"])
    try:
        parsed = await fetch_feed(url)
        if parsed.bozo and not parsed.entries:
            await reply.edit_text(msg["parse_failed"].format(url=url))
            return
    except Exception as e:
        await reply.edit_text(msg["fetch_failed"].format(error=e))
        return

    feed_title = parsed.feed.get("title", url)

    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO feeds (url, title) VALUES (?, ?)",
            (url, feed_title),
        )
        cursor = await db.execute("SELECT id FROM feeds WHERE url = ?", (url,))
        feed = await cursor.fetchone()
        feed_id = feed["id"]

        try:
            await db.execute(
                "INSERT INTO subscriptions (feed_id, chat_id, chat_type) VALUES (?, ?, ?)",
                (feed_id, chat_id, chat_type),
            )
            await db.commit()
        except sqlite3.IntegrityError:
            await reply.edit_text(msg["already_subscribed"].format(title=feed_title))
            return

    # Seed entries and push recent ones to subscriber
    seeded = await seed_feed_entries(feed_id, parsed)
    await reply.edit_text(msg["subscribed"].format(title=feed_title, feed_id=feed_id))

    # Push the seeded entries to this chat
    from feedpulse.scheduler import _build_message
    limit = settings.initial_fetch_limit
    entries = parsed.entries[:limit] if limit > 0 else parsed.entries
    for entry in entries:
        title = entry.get("title", "No title")
        link = entry.get("link", "")
        text = _build_message(feed_title, {"title": title, "link": link})
        try:
            await ctx.bot.send_message(
                chat_id=chat_id, text=text, parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Failed to send initial entry: {e}")


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT f.id, f.title, f.url, f.last_checked_at
            FROM feeds f
            JOIN subscriptions s ON s.feed_id = f.id
            WHERE s.chat_id = ?
            ORDER BY f.id
            """,
            (chat_id,),
        )
        feeds = await cursor.fetchall()

    if not feeds:
        await update.message.reply_text(msg["no_subscriptions"])
        return

    lines = [msg["subscriptions_header"]]
    for f in feeds:
        title = f["title"] or f["url"]
        lines.append(f"  [{f['id']}] {title}")
    await update.message.reply_text("\n".join(lines))


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text(msg["remove_usage"])
        return

    try:
        feed_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text(msg["id_must_be_number"])
        return

    chat_id = update.effective_chat.id
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE feed_id = ? AND chat_id = ?",
            (feed_id, chat_id),
        )
        await db.commit()
        if cursor.rowcount > 0:
            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM subscriptions WHERE feed_id = ?", (feed_id,)
            )
            row = await cursor2.fetchone()
            if row["cnt"] == 0:
                await db.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
                await db.commit()
            await update.message.reply_text(msg["unsubscribed"].format(feed_id=feed_id))
        else:
            await update.message.reply_text(msg["not_found"].format(feed_id=feed_id))


async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger a check for the current chat's subscriptions only."""
    from feedpulse.scheduler import notify_subscribers

    chat_id = update.effective_chat.id
    await update.message.reply_text(msg["checking"])
    count = await notify_subscribers(ctx.bot, chat_id=chat_id)
    await update.message.reply_text(msg["check_done"].format(count=count))


def create_bot() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("check", cmd_check))
    return app
