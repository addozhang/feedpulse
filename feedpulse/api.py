"""FastAPI REST API for FeedPulse."""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from feedpulse.db import get_db
from feedpulse.fetcher import check_feed_updates, fetch_feed, seed_feed_entries

logger = logging.getLogger(__name__)

app = FastAPI(title="FeedPulse API", version="0.1.0")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FeedCreate(BaseModel):
    url: str
    chat_id: int
    chat_type: str = "private"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Feeds
# ---------------------------------------------------------------------------

@app.get("/api/feeds")
async def list_feeds():
    """List all feeds."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, url, title, last_checked_at, created_at FROM feeds ORDER BY id"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@app.post("/api/feeds", status_code=201)
async def add_feed(body: FeedCreate):
    """Add a new feed and subscribe the given chat."""
    # Validate the feed URL
    try:
        parsed = await fetch_feed(body.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch feed: {e}")

    if parsed.bozo and not parsed.entries:
        raise HTTPException(status_code=400, detail=f"Failed to parse feed: {body.url}")

    feed_title = parsed.feed.get("title", body.url)

    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO feeds (url, title) VALUES (?, ?)",
            (body.url, feed_title),
        )
        cursor = await db.execute("SELECT id FROM feeds WHERE url = ?", (body.url,))
        feed = await cursor.fetchone()
        feed_id = feed["id"]

        try:
            await db.execute(
                "INSERT INTO subscriptions (feed_id, chat_id, chat_type) VALUES (?, ?, ?)",
                (feed_id, body.chat_id, body.chat_type),
            )
        except Exception:
            # Subscription already exists — not an error
            pass
        await db.commit()

    await seed_feed_entries(feed_id, parsed)

    return {"id": feed_id, "url": body.url, "title": feed_title}


@app.delete("/api/feeds/{feed_id}")
async def delete_feed(feed_id: int):
    """Delete a feed and all its entries and subscriptions (CASCADE)."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM feeds WHERE id = ?", (feed_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

        await db.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        await db.commit()

    return {"detail": f"Feed {feed_id} deleted"}


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------

@app.get("/api/feeds/{feed_id}/entries")
async def list_entries(feed_id: int):
    """List entries for a feed."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM feeds WHERE id = ?", (feed_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

        cursor = await db.execute(
            "SELECT id, feed_id, entry_id, title, link, published_at, created_at "
            "FROM entries WHERE feed_id = ? ORDER BY id DESC",
            (feed_id,),
        )
        rows = await cursor.fetchall()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

@app.get("/api/subscriptions")
async def list_subscriptions(chat_id: int):
    """List subscriptions for a chat."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT s.id, s.feed_id, s.chat_id, s.chat_type, s.created_at, "
            "f.url, f.title "
            "FROM subscriptions s "
            "JOIN feeds f ON f.id = s.feed_id "
            "WHERE s.chat_id = ? ORDER BY s.id",
            (chat_id,),
        )
        rows = await cursor.fetchall()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Feed check
# ---------------------------------------------------------------------------

@app.post("/api/feeds/{feed_id}/check")
async def trigger_check(feed_id: int):
    """Trigger a check for a specific feed."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id, url FROM feeds WHERE id = ?", (feed_id,))
        feed = await cursor.fetchone()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    new_entries = await check_feed_updates(feed["id"], feed["url"])
    return {"feed_id": feed_id, "new_entries": len(new_entries), "entries": new_entries}
