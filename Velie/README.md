# Velie — AI Code Review Agent

> RYKNSH records 品質保証AI ① — PRが来たら自動でコードレビューするBot

## Architecture

```
GitHub PR Event → Webhook POST → FastAPI → LangGraph Agent → PR Comment
                                    │
                              fetch_diff → review_code (Claude) → post_review
```

## Quick Start

### 1. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して3つのキーを設定
```

| 変数名 | 説明 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude API キー |
| `GITHUB_TOKEN` | GitHub PAT（`repo` スコープ） |
| `GITHUB_WEBHOOK_SECRET` | Webhook 署名検証用シークレット |

### 2. 起動

```bash
# 依存インストール
uv sync

# サーバー起動
uv run python main.py
```

### 3. GitHub Webhook設定

1. リポジトリ → Settings → Webhooks → Add webhook
2. Payload URL: `https://your-domain/webhook/github`
3. Content type: `application/json`
4. Secret: `.env` の `GITHUB_WEBHOOK_SECRET` と同じ値
5. Events: **Pull requests** のみ

### 4. テスト

```bash
uv run pytest tests/ -v
```

## Docker

```bash
docker build -t velie .
docker run --env-file .env -p 8000:8000 velie
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | ヘルスチェック |
| `POST` | `/webhook/github` | GitHub Webhook受信 |

## Tech Stack

- **LangGraph** — Stateful AI Agent Graph
- **Claude** (langchain-anthropic) — コードレビュー LLM
- **FastAPI** — Webhook受信サーバー
- **httpx** — GitHub API通信
