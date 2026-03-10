# FeedPulse 🔔

Self-hosted RSS/Feed subscription service with Telegram Bot integration.

## Features

- RSS/Atom feed management (add, list, remove)
- Periodic polling for new content (default: every 10 minutes)
- Push new articles to Telegram (private chat, group, or channel)
- SQLite storage, lightweight deployment
- Configurable initial fetch limit on subscribe

## Quick Start

### Docker Compose (Recommended)

```bash
cp .env.example .env
# Edit .env, set your Telegram Bot Token
docker compose up -d
```

### Local

```bash
pip install -e .
export FEEDPULSE_TELEGRAM_BOT_TOKEN=your-token
python -m feedpulse.main
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show help |
| `/add <url>` | Subscribe to an RSS feed |
| `/list` | List current subscriptions |
| `/remove <id>` | Unsubscribe |
| `/check` | Check for updates now |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `FEEDPULSE_TELEGRAM_BOT_TOKEN` | — | Telegram Bot Token (required) |
| `FEEDPULSE_POLL_INTERVAL_MINUTES` | `10` | Polling interval in minutes |
| `FEEDPULSE_INITIAL_FETCH_LIMIT` | `5` | Number of recent entries to push on subscribe |
| `FEEDPULSE_MAX_CONCURRENT_FEEDS` | `10` | Max concurrent feed fetches |
| `FEEDPULSE_DB_PATH` | `data/feedpulse.db` | Database path |
| `FEEDPULSE_LOG_LEVEL` | `INFO` | Log level |

## Roadmap

- [ ] Web UI
- [ ] WebSub support
- [ ] Feed grouping / tags
- [ ] Full-text fetching
- [ ] OPML import/export
