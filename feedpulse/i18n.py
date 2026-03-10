"""Internationalization support."""

MESSAGES = {
    "en": {
        "help": (
            "🔔 FeedPulse — RSS Feed Notifications\n\n"
            "Commands:\n"
            "/add <url> — Subscribe to a feed\n"
            "/list — List subscriptions\n"
            "/remove <id> — Unsubscribe\n"
            "/check — Check for updates now"
        ),
        "add_usage": "Usage: /add <feed_url>",
        "validating": "⏳ Validating feed...",
        "parse_failed": "❌ Failed to parse feed: {url}",
        "fetch_failed": "❌ Fetch failed: {error}",
        "already_subscribed": "⚠️ Already subscribed: {title}",
        "subscribed": "✅ Subscribed: {title}\nID: {feed_id}",
        "no_subscriptions": "📭 No subscriptions",
        "subscriptions_header": "📋 Subscriptions:\n",
        "remove_usage": "Usage: /remove <feed_id>",
        "id_must_be_number": "❌ ID must be a number",
        "unsubscribed": "✅ Unsubscribed ID: {feed_id}",
        "not_found": "❌ Subscription not found: {feed_id}",
        "checking": "🔍 Checking for updates...",
        "check_done": "✅ Done. Pushed {count} new entries.",
        "cmd_start": "Show help",
        "cmd_add": "Subscribe to an RSS feed",
        "cmd_list": "List subscriptions",
        "cmd_remove": "Unsubscribe",
        "cmd_check": "Check for updates now",
    },
    "zh": {
        "help": (
            "🔔 FeedPulse — RSS 订阅推送\n\n"
            "命令：\n"
            "/add <url> — 添加订阅\n"
            "/list — 查看订阅列表\n"
            "/remove <id> — 删除订阅\n"
            "/check — 立即检查更新"
        ),
        "add_usage": "用法: /add <feed_url>",
        "validating": "⏳ 正在验证 feed...",
        "parse_failed": "❌ 无法解析 feed: {url}",
        "fetch_failed": "❌ 获取失败: {error}",
        "already_subscribed": "⚠️ 已经订阅过了: {title}",
        "subscribed": "✅ 已订阅: {title}\nID: {feed_id}",
        "no_subscriptions": "📭 没有订阅",
        "subscriptions_header": "📋 当前订阅：\n",
        "remove_usage": "用法: /remove <feed_id>",
        "id_must_be_number": "❌ ID 必须是数字",
        "unsubscribed": "✅ 已取消订阅 ID: {feed_id}",
        "not_found": "❌ 未找到订阅 ID: {feed_id}",
        "checking": "🔍 正在检查更新...",
        "check_done": "✅ 检查完成，推送了 {count} 条新内容",
        "cmd_start": "查看帮助",
        "cmd_add": "添加 RSS 订阅",
        "cmd_list": "查看订阅列表",
        "cmd_remove": "取消订阅",
        "cmd_check": "立即检查更新",
    },
}


def get_messages(lang: str) -> dict[str, str]:
    """Get message dict for a language, fallback to English."""
    return MESSAGES.get(lang, MESSAGES["en"])
