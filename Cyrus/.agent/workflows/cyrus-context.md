---
description: Cyrusのアーキテクチャと設計を素早く把握するためのコンテキストロード
---

# Cyrus コンテキストロード

// turbo-all

## このコマンドを使うとき
- 新しいセッション開始時
- 久しぶりにCyrusに戻ってきたとき
- 方向性を見失ったとき

## Step 1: 全体像

```
cat /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus/WHITEPAPER.md | head -100
```

### Cyrusの本質
- **自律グロースエンジン**: マーケ戦略→営業→クロージング→効果測定を全自動
- **23ノード / 4レイヤー**: Intelligence → Acquisition → Conversion → Evolution
- **3ビジネスモデル対応**: B2B / B2C / C2C（+ B2C高額 = B2Bハイブリッド）
- **Entity Model v3**: Organization / Individual / Creator（全ジャンル包摂）

## Step 2: 現在のプロジェクト構造

```
find /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus -name "*.py" | head -40
```

## Step 3: テスト状態確認

```
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus && uv run pytest tests/ -v --tb=no -q
```

## Step 4: ロードマップ確認

```
cat /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus/ROADMAP.md 2>/dev/null || echo "ROADMAP.md未作成 — WHITEPAPERのセクション12を参照"
```

## クイックリファレンス

### 4レイヤー & 23ノード

| Layer | ノード |
|-------|--------|
| 🔵 Intelligence (3) | market_scanner, icp_profiler, signal_detector |
| 🟢 Acquisition (7) | inbound_magnet, content_architect, outbound_personalizer, viral_engineer, campaign_orchestrator, community_seeder, ad_optimizer |
| 🟡 Conversion (11) | trust_engine (横断), nurture_sequencer, proposal_generator, meeting_setter, close_advisor, activation_optimizer, retention_looper, monetization_trigger, onboarding_sequencer, trust_builder, marketplace_growth_driver |
| 🔴 Evolution (2) | performance_analyst, ab_optimizer |

### 技術スタック
- **グラフ**: LangGraph StateGraph
- **API**: FastAPI (port 8001)
- **LLM**: Ada Core API経由
- **DB**: Supabase (pgvector, RLS)
- **テスト**: pytest + pytest-asyncio

### 設計パターン
- **CyrusNode基底**: engine/base.py — 全ノード共通
- **Adapter Pattern**: Entity Type別の処理分岐
- **Strategy Pattern**: conversion_mode + deal_complexityでパイプライン選択
- **Priority Weights**: Outcome(0.40) > Quality(0.30) > Speed(0.20) > Cost(0.10)

### セールスメソッド
- B2B: Challenger → SPIN → Consultative → MEDDIC
- B2C: PASTOR法
- B2C高額: B2Bハイブリッド (deal_complexity: high)
- C2C: コミュニティ駆動

### Trust Engine 5機能
1. Personality Profiler（データ取得3階層: 確実→許諾→推定→自動補正）
2. Interaction Memory（全タッチポイント永続記憶）
3. Value-First Strategist（売る前に無償提供）
4. Timing Optimizer（今連絡すべきか判断）
5. Trust Score Tracker（0-100 → 知人→好意→信頼→パートナー）

### 価格モデル
- Free / Usage / Growth / **Full Outcome (15-35%)** / Blueprint Design
- API原価控除（売上5%キャップ）
