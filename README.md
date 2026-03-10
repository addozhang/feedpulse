# FeedPulse 🔔

Self-hosted RSS/Feed 订阅推送，通过 Telegram Bot 管理和接收更新。

## 功能

- RSS/Atom Feed 订阅管理（添加、查看、删除）
- 定时轮询（默认 10 分钟）检测新内容
- 新文章自动推送到 Telegram（私聊、群组、频道均支持）
- SQLite 持久化，轻量部署

## 快速开始

### Docker Compose（推荐）

```bash
cp .env.example .env
# 编辑 .env，填入 Telegram Bot Token
docker compose up -d
```

### 本地运行

```bash
pip install -e .
export FEEDPULSE_TELEGRAM_BOT_TOKEN=your-token
python -m feedpulse.main
```

## Bot 命令

| 命令 | 说明 |
|------|------|
| `/start` | 查看帮助 |
| `/add <url>` | 添加 RSS 订阅 |
| `/list` | 查看当前订阅 |
| `/remove <id>` | 取消订阅 |
| `/check` | 立即检查更新 |

## 配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `FEEDPULSE_TELEGRAM_BOT_TOKEN` | — | Telegram Bot Token（必填） |
| `FEEDPULSE_POLL_INTERVAL_MINUTES` | `10` | 轮询间隔（分钟） |
| `FEEDPULSE_DB_PATH` | `data/feedpulse.db` | 数据库路径 |
| `FEEDPULSE_LOG_LEVEL` | `INFO` | 日志级别 |

## Roadmap

- [ ] Web UI
- [ ] WebSub 支持
- [ ] Feed 分组/标签
- [ ] 全文抓取
- [ ] OPML 导入导出
