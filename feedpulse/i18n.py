"""Internationalization support."""

MESSAGES = {
    "en": {
        "help": (
            "🔔 FeedPulse — RSS Feed Notifications\n\n"
            "Commands:\n"
            "/add <url> — Subscribe to a feed\n"
            "/list — List subscriptions\n"
            "/remove <id> — Unsubscribe\n"
            "/check — Check for updates now\n"
            "/export — Export subscriptions as OPML\n"
            "/import — Import an attached or replied-to OPML file"
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
        "cmd_info": "Show chat info",
        "cmd_export": "Export subscriptions as OPML",
        "cmd_import": "Import subscriptions from OPML",
        "export_done": "Exported {count} subscriptions.",
        "import_usage": "Attach an OPML file with /import, or reply to one with /import.",
        "import_too_large": "❌ OPML file must be 1 MB or smaller.",
        "importing": "⏳ Importing subscriptions...",
        "import_invalid": "❌ Invalid OPML file: {error}",
        "import_download_failed": "❌ Failed to download OPML file: {error}",
        "import_empty": "📭 No feeds found in the OPML file.",
        "import_done": "✅ Import complete. Added: {added}, skipped: {skipped}, failed: {failed}.",
        "info": (
            "ℹ️ Chat Info\n\n"
            "Chat ID: <code>{chat_id}</code>\n"
            "Chat Type: {chat_type}\n"
            "Subscriptions: {sub_count}\n"
            "Total Entries: {entry_count}"
        ),
    },
    "zh": {
        "help": (
            "🔔 FeedPulse — RSS 订阅推送\n\n"
            "命令：\n"
            "/add <url> — 添加订阅\n"
            "/list — 查看订阅列表\n"
            "/remove <id> — 删除订阅\n"
            "/check — 立即检查更新\n"
            "/export — 导出 OPML 订阅\n"
            "/import — 导入附带或回复的 OPML 文件"
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
        "cmd_info": "查看聊天信息",
        "cmd_export": "导出 OPML 订阅",
        "cmd_import": "从 OPML 导入订阅",
        "export_done": "已导出 {count} 个订阅。",
        "import_usage": "请在 /import 消息中附带 OPML 文件，或回复 OPML 文件发送 /import。",
        "import_too_large": "❌ OPML 文件不能超过 1 MB。",
        "importing": "⏳ 正在导入订阅...",
        "import_invalid": "❌ OPML 文件无效: {error}",
        "import_download_failed": "❌ 下载 OPML 文件失败: {error}",
        "import_empty": "📭 OPML 文件中没有 Feed。",
        "import_done": "✅ 导入完成。新增: {added}，跳过: {skipped}，失败: {failed}。",
        "info": (
            "ℹ️ 聊天信息\n\n"
            "Chat ID: <code>{chat_id}</code>\n"
            "聊天类型: {chat_type}\n"
            "订阅数: {sub_count}\n"
            "文章总数: {entry_count}"
        ),
    },
}


def get_messages(lang: str) -> dict[str, str]:
    """Get message dict for a language, fallback to English."""
    return MESSAGES.get(lang, MESSAGES["en"])
