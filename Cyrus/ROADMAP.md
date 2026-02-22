# Cyrus ROADMAP — 自律グロースエンジン開発ロードマップ

> Whitepaper v3.1 セクション12準拠（23ノード / 4レイヤー / 34ラウンドディベート完走）

---

## 全体ロードマップ

```
 10 ████░░░░░░░░░░░░░░░░ Sprint 1 ✅ Intelligence MVP
 30 ████████░░░░░░░░░░░░ Sprint 2 ← NOW: Trust + Outbound + Inbound
 45 ████████████░░░░░░░░ Sprint 3: Content & Campaign
 60 ████████████████░░░░ Sprint 4: Conversion Full (B2B+B2C+C2C)
 85 ████████████████████ Sprint 5: Evolution + 内販統合 + Full Outcome
 90 █████████████████████ Sprint 6: 外販PLG Launch
```

---

## ✅ Sprint 1: Intelligence Layer MVP — 戦闘力 10/100

**完了: 2026-02-22 | Commit: `022bd33`**

| 成果物 | 状態 |
|--------|------|
| `engine/base.py` — CyrusNode基底 | ✅ |
| `engine/state.py` — CyrusState | ✅ |
| `engine/graph.py` — Intelligence LangGraph | ✅ |
| `models/entity.py` — Entity Model v3 | ✅ |
| `models/blueprint.py` — GrowthBlueprint v3 | ✅ |
| `nodes/intelligence/market_scanner.py` | ✅ |
| `nodes/intelligence/icp_profiler.py` | ✅ |
| `nodes/intelligence/signal_detector.py` | ✅ |
| `server/app.py` + routes | ✅ |
| `migrations/001_initial.sql` | ✅ |
| **テスト: 30/30 passed** | ✅ |

---

## 🔧 Sprint 2: Trust Engine + Outbound + Inbound — 戦闘力 30/100

**ターゲット: M2 W2**

### ノード

| ノード | レイヤー | 概要 |
|--------|---------|------|
| `trust_engine` | 🟡 Conversion (横断) | Personality Profiler + Interaction Memory + Value-First Strategist + Timing Optimizer + Trust Score Tracker |
| `outbound_personalizer` | 🟢 Acquisition | L3パーソナライズメール/DM/InMail。Trust Engine連携 |
| `inbound_magnet` | 🟢 Acquisition | Always-On呼び水エンジン。知的資産公開 + イベント駆動接点 + コミュニティ常駐 |

### タスク

- [ ] `nodes/conversion/trust_engine.py` — 5機能実装
  - [ ] Personality Profiler（データ取得3階層 + 推定→補正ループ）
  - [ ] Interaction Memory（pgvector永続記憶）
  - [ ] Value-First Strategist（Ada API連携）
  - [ ] Timing Optimizer
  - [ ] Trust Score Tracker（0-100, 4段階）
- [ ] `nodes/acquisition/outbound_personalizer.py`
  - [ ] L1/L2/L3パーソナライズ生成
  - [ ] Trust Engine連携（Personality→トーン、Timing→送信判断）
- [ ] `nodes/acquisition/inbound_magnet.py`
  - [ ] 知的資産自動生成（Intelligence Layer出力→レポート化）
  - [ ] イベント駆動型接点（シグナル検知→呼び水配信）
- [ ] グラフ拡張: Intelligence → Trust → Acquisition パイプライン
- [ ] テスト: trust_engine / outbound / inbound / 統合
- [ ] `migrations/002_trust_engine.sql` — interaction_memory / trust_scores テーブル

---

## Sprint 3: Content & Campaign — 戦闘力 45/100

**ターゲット: M2 W3**

| ノード | レイヤー | 概要 |
|--------|---------|------|
| `content_architect` | 🟢 Acquisition | SEOブログ + バイラル動画 + LP + ケーススタディ。PASTOR法統合。Lumina連携 |
| `campaign_orchestrator` | 🟢 Acquisition | マルチチャネルキャンペーンの同時制御 |
| `viral_engineer` | 🟢 Acquisition | バイラルフック設計。トレンド分析→UGC促進 |
| `ad_optimizer` | 🟢 Acquisition | Meta/Google/TikTok広告の自律最適配分 |

---

## Sprint 4: Conversion Full — 戦闘力 60/100

**ターゲット: M2 W4**

### B2B Pipeline
| ノード | 概要 |
|--------|------|
| `nurture_sequencer` | ステップメール・フォローアップ自動化 |
| `proposal_generator` | 提案書のAI自動生成（Ada + Lumina連携） |
| `meeting_setter` | カレンダー連携・商談セッティング |
| `close_advisor` | Gong連携・クロージング支援 |

### B2C Pipeline
| ノード | 概要 |
|--------|------|
| `activation_optimizer` | 初回体験最適化・Aha Moment設計 |
| `retention_looper` | D1/D7/D30リテンション・チャーン予測 |
| `monetization_trigger` | フリーミアム→有料転換の最適タイミング |

### C2C Pipeline
| ノード | 概要 |
|--------|------|
| `onboarding_sequencer` | Supply/Demand両サイド初回体験 |
| `trust_builder` | プラットフォーム信頼構築・レビューシステム |
| `marketplace_growth_driver` | 需給バランス動的調整 |

---

## Sprint 5: Evolution + 内販統合 — 戦闘力 85/100

**ターゲット: M3**

| ノード | 概要 |
|--------|------|
| `performance_analyst` | 全チャネル統合KPI。CAC/LTV/DAU/Retention/GMV |
| `ab_optimizer` | A/Bテスト自動実行→勝者採用→Intelligence再計算 |

- [ ] RYKNSH 6社の内販Blueprint設定
- [ ] Full Outcome課金フロー（Stripe Webhook連携）
- [ ] API原価控除計算（5%キャップ）
- [ ] ダッシュボード

---

## Sprint 6: 外販PLG Launch — 戦闘力 90/100

**ターゲット: M4**

- [ ] Free Tier（月100リード/10キャンペーン）
- [ ] セルフサーブオンボーディング
- [ ] Product Hunt ローンチ
- [ ] MRR ¥100万 / 30有料テナント

---

## KPI

### 外販
| 指標 | 目標（M4） |
|------|------------|
| MRR | ¥100万 |
| 有料テナント | 30社 |
| Free Tier | 500社 |
| Free→Paid CVR | 6%+ |
| Full Outcome | 5社 |

### 内販
| 指標 | B2B | B2C | C2C |
|------|-----|-----|-----|
| 新規リード/月 | 500 | — | — |
| 新規ユーザー/月 | — | 10,000 | — |
| 新規クリエイター/月 | — | — | 100 |
| Trust Score平均 | 70+ | 60+ | 55+ |

---

> **最終更新**: 2026-02-23
> **現在地**: Sprint 2（Trust Engine + Outbound + Inbound）
> **戦闘力**: 10/100 → 30/100へ
