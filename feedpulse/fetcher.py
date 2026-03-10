import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
import feedparser

from feedpulse.config import settings
from feedpulse.db import get_db

logger = logging.getLogger(__name__)


async def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """Fetch and parse a feed URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status >= 400:
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history,
                    status=resp.status, message=f"HTTP {resp.status}",
                )
            body = await resp.text()
    return await asyncio.to_thread(feedparser.parse, body)


async def check_feed_updates(feed_id: int, url: str) -> list[dict]:
    """Check a feed for new entries. Returns list of new entries."""
    try:
        parsed = await fetch_feed(url)
    except Exception as e:
        logger.error(f"Error fetching feed {url}: {e}")
        return []

    if parsed.bozo and not parsed.entries:
        logger.warning(f"Feed {url} parse error: {parsed.bozo_exception}")
        return []

    new_entries = []
    async with get_db() as db:
        # Update feed title if available
        if parsed.feed.get("title"):
            await db.execute(
                "UPDATE feeds SET title = ? WHERE id = ?",
                (parsed.feed.title, feed_id),
            )

        # Get last_checked_at for time-based filtering
        cursor = await db.execute(
            "SELECT last_checked_at FROM feeds WHERE id = ?", (feed_id,)
        )
        row = await cursor.fetchone()
        last_checked = row["last_checked_at"] if row else None

        for entry in parsed.entries:
            entry_id = entry.get("id") or entry.get("link") or entry.get("title", "")
            if not entry_id:
                continue

            published = entry.get("published") or entry.get("updated") or ""

            # Time-based filter: skip entries older than last check
            if last_checked and published:
                from email.utils import parsedate_to_datetime
                try:
                    pub_dt = parsedate_to_datetime(published)
                    check_dt = datetime.fromisoformat(last_checked)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    if check_dt.tzinfo is None:
                        check_dt = check_dt.replace(tzinfo=timezone.utc)
                    if pub_dt <= check_dt:
                        continue
                except (ValueError, TypeError):
                    pass  # Fall through to entry_id dedup

            # Fallback: entry_id dedup for entries without valid timestamps
            cursor = await db.execute(
                "SELECT id FROM entries WHERE feed_id = ? AND entry_id = ?",
                (feed_id, entry_id),
            )
            if await cursor.fetchone():
                continue

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


async def seed_feed_entries(feed_id: int, parsed: feedparser.FeedParserDict) -> int:
    """Pre-populate ALL entries for a newly added feed so they won't be pushed as new.
    Returns number of entries seeded."""
    count = 0
    async with get_db() as db:
        for entry in parsed.entries:
            entry_id = entry.get("id") or entry.get("link") or entry.get("title", "")
            if not entry_id:
                continue
            published = entry.get("published") or entry.get("updated") or ""
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            await db.execute(
                "INSERT OR IGNORE INTO entries (feed_id, entry_id, title, link, published_at) VALUES (?, ?, ?, ?, ?)",
                (feed_id, entry_id, title, link, published),
            )
            count += 1
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("UPDATE feeds SET last_checked_at = ? WHERE id = ?", (now, feed_id))
        await db.commit()
    return count


async def check_all_feeds(
    chat_id: int | None = None,
) -> dict[int, list[dict]]:
    """Check feeds for updates. If chat_id given, only check that chat's subscriptions."""
    async with get_db() as db:
        if chat_id is not None:
            cursor = await db.execute(
                "SELECT f.id, f.url FROM feeds f "
                "JOIN subscriptions s ON s.feed_id = f.id "
                "WHERE s.chat_id = ?",
                (chat_id,),
            )
        else:
            cursor = await db.execute("SELECT id, url FROM feeds")
        feeds = await cursor.fetchall()

    sem = asyncio.Semaphore(settings.max_concurrent_feeds)

    async def _check(feed_id: int, url: str) -> tuple[int, list[dict]]:
        async with sem:
            entries = await check_feed_updates(feed_id, url)
            return feed_id, entries

    tasks = [_check(f["id"], f["url"]) for f in feeds]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results = {}
    for r in results_list:
        if isinstance(r, Exception):
            logger.error(f"Feed check failed: {r}")
            continue
        feed_id, entries = r
        if entries:
            results[feed_id] = entries

    return results
