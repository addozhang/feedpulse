import logging
from datetime import datetime, timezone

import aiohttp
import feedparser

from feedpulse.db import get_db

logger = logging.getLogger(__name__)


async def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """Fetch and parse a feed URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            body = await resp.text()
    return feedparser.parse(body)


async def check_feed_updates(feed_id: int, url: str) -> list[dict]:
    """Check a feed for new entries. Returns list of new entries."""
    db = await get_db()
    try:
        parsed = await fetch_feed(url)
        if parsed.bozo and not parsed.entries:
            logger.warning(f"Feed {url} returned error: {parsed.bozo_exception}")
            return []

        # Update feed title if available
        if parsed.feed.get("title"):
            await db.execute("UPDATE feeds SET title = ? WHERE id = ?", (parsed.feed.title, feed_id))

        new_entries = []
        for entry in parsed.entries:
            entry_id = entry.get("id") or entry.get("link") or entry.get("title", "")
            if not entry_id:
                continue

            # Check if we already have this entry
            cursor = await db.execute(
                "SELECT id FROM entries WHERE feed_id = ? AND entry_id = ?",
                (feed_id, entry_id),
            )
            existing = await cursor.fetchone()
            if existing:
                continue

            published = entry.get("published") or entry.get("updated") or ""
            title = entry.get("title", "No title")
            link = entry.get("link", "")

            await db.execute(
                "INSERT INTO entries (feed_id, entry_id, title, link, published_at) VALUES (?, ?, ?, ?, ?)",
                (feed_id, entry_id, title, link, published),
            )
            new_entries.append({"title": title, "link": link, "published": published})

        now = datetime.now(timezone.utc).isoformat()
        await db.execute("UPDATE feeds SET last_checked_at = ? WHERE id = ?", (now, feed_id))
        await db.commit()

        return new_entries
    except Exception as e:
        logger.error(f"Error fetching feed {url}: {e}")
        return []
    finally:
        await db.close()


async def check_all_feeds() -> dict[int, list[dict]]:
    """Check all feeds for updates. Returns {feed_id: [new_entries]}."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, url FROM feeds")
        feeds = await cursor.fetchall()
    finally:
        await db.close()

    results = {}
    for feed in feeds:
        new_entries = await check_feed_updates(feed["id"], feed["url"])
        if new_entries:
            results[feed["id"]] = new_entries

    return results
