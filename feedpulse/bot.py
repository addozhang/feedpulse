import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from feedpulse.config import settings
from feedpulse.db import get_db
from feedpulse.fetcher import fetch_feed

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔔 FeedPulse — RSS 订阅推送\n\n"
        "命令：\n"
        "/add <url> — 添加订阅\n"
        "/list — 查看订阅列表\n"
        "/remove <id> — 删除订阅\n"
        "/check — 立即检查更新"
    )


async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("用法: /add <feed_url>")
        return

    url = ctx.args[0].strip()
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    # Validate feed
    msg = await update.message.reply_text(f"⏳ 正在验证 feed...")
    try:
        parsed = await fetch_feed(url)
        if parsed.bozo and not parsed.entries:
            await msg.edit_text(f"❌ 无法解析 feed: {url}")
            return
    except Exception as e:
        await msg.edit_text(f"❌ 获取失败: {e}")
        return

    feed_title = parsed.feed.get("title", url)

    db = await get_db()
    try:
        # Upsert feed
        await db.execute(
            "INSERT OR IGNORE INTO feeds (url, title) VALUES (?, ?)",
            (url, feed_title),
        )
        cursor = await db.execute("SELECT id FROM feeds WHERE url = ?", (url,))
        feed = await cursor.fetchone()
        feed_id = feed["id"]

        # Add subscription
        try:
            await db.execute(
                "INSERT INTO subscriptions (feed_id, chat_id, chat_type) VALUES (?, ?, ?)",
                (feed_id, chat_id, chat_type),
            )
            await db.commit()
            await msg.edit_text(f"✅ 已订阅: {feed_title}\nID: {feed_id}")
        except Exception:
            await msg.edit_text(f"⚠️ 已经订阅过了: {feed_title}")
    finally:
        await db.close()


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    db = await get_db()
    try:
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
    finally:
        await db.close()

    if not feeds:
        await update.message.reply_text("📭 没有订阅")
        return

    lines = ["📋 当前订阅：\n"]
    for f in feeds:
        title = f["title"] or f["url"]
        lines.append(f"  [{f['id']}] {title}")
    await update.message.reply_text("\n".join(lines))


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("用法: /remove <feed_id>")
        return

    try:
        feed_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID 必须是数字")
        return

    chat_id = update.effective_chat.id
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE feed_id = ? AND chat_id = ?",
            (feed_id, chat_id),
        )
        await db.commit()
        if cursor.rowcount > 0:
            # Clean up feed if no more subscribers
            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM subscriptions WHERE feed_id = ?", (feed_id,)
            )
            row = await cursor2.fetchone()
            if row["cnt"] == 0:
                await db.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
                await db.commit()
            await update.message.reply_text(f"✅ 已取消订阅 ID: {feed_id}")
        else:
            await update.message.reply_text(f"❌ 未找到订阅 ID: {feed_id}")
    finally:
        await db.close()


async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger a check for the current chat's subscriptions."""
    from feedpulse.scheduler import notify_subscribers

    await update.message.reply_text("🔍 正在检查更新...")
    count = await notify_subscribers(ctx.bot)
    await update.message.reply_text(f"✅ 检查完成，推送了 {count} 条新内容")


def create_bot() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("check", cmd_check))
    return app
