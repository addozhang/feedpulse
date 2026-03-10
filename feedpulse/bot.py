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

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔔 FeedPulse — RSS Feed Notifications\n\n"
        "Commands:\n"
        "/add <url> — Subscribe to a feed\n"
        "/list — List subscriptions\n"
        "/remove <id> — Unsubscribe\n"
        "/check — Check for updates now"
    )


async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /add <feed_url>")
        return

    url = ctx.args[0].strip()
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    msg = await update.message.reply_text("⏳ Validating feed...")
    try:
        parsed = await fetch_feed(url)
        if parsed.bozo and not parsed.entries:
            await msg.edit_text(f"❌ Failed to parse feed: {url}")
            return
    except Exception as e:
        await msg.edit_text(f"❌ Fetch failed: {e}")
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
            await msg.edit_text(f"⚠️ Already subscribed: {feed_title}")
            return

    # Seed entries and push recent ones to subscriber
    seeded = await seed_feed_entries(feed_id, parsed)
    await msg.edit_text(f"✅ Subscribed: {feed_title}\nID: {feed_id}")

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
        await update.message.reply_text("📭 No subscriptions")
        return

    lines = ["📋 Subscriptions:\n"]
    for f in feeds:
        title = f["title"] or f["url"]
        lines.append(f"  [{f['id']}] {title}")
    await update.message.reply_text("\n".join(lines))


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /remove <feed_id>")
        return

    try:
        feed_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID must be a number")
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
            await update.message.reply_text(f"✅ Unsubscribed ID: {feed_id}")
        else:
            await update.message.reply_text(f"❌ Subscription not found: {feed_id}")


async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger a check for the current chat's subscriptions only."""
    from feedpulse.scheduler import notify_subscribers

    chat_id = update.effective_chat.id
    await update.message.reply_text("🔍 Checking for updates...")
    count = await notify_subscribers(ctx.bot, chat_id=chat_id)
    await update.message.reply_text(f"✅ Done. Pushed {count} new entries.")


def create_bot() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("check", cmd_check))
    return app
