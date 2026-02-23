# Cyrus ROADMAP — 自律グロースエンジン開発ロードマップ

> Whitepaper v3.1 セクション12準拠（23ノード / 4レイヤー / 34ラウンドディベート完走）

---

## 全体ロードマップ

```
 10 ████░░░░░░░░░░░░░░░░ Sprint 1 ✅ Intelligence MVP
 30 ████████░░░░░░░░░░░░ Sprint 2 ✅ Trust + Outbound + Inbound
 45 ████████████░░░░░░░░ Sprint 3 ✅ Content & Campaign
 60 ████████████████░░░░ Sprint 4 ✅ Conversion Full (B2B+B2C+C2C)
 85 ████████████████████ Sprint 5 ✅ Evolution + All 23 Nodes
 90 █████████████████████ Sprint 6 ✅ PLG Launch API ← CURRENT
```

---

## ✅ Sprint 1: Intelligence Layer MVP — 戦闘力 10/100

**完了: 2026-02-22 | Commit: `022bd33` | テスト: 30/30**

- `engine/base.py` — CyrusNode基底
- `engine/state.py` / `engine/graph.py`
- `models/entity.py` — Entity Model v3 / `models/blueprint.py`
- `nodes/intelligence/` — market_scanner / icp_profiler / signal_detector
- `server/app.py` + routes / `migrations/001_initial.sql`

---

## ✅ Sprint 2: Trust Engine + Outbound + Inbound — 戦闘力 30/100

**完了: 2026-02-22 | Commit: `33043e3` | テスト: 44/44**

- `nodes/conversion/trust_engine.py` — 5機能(Personality/Memory/Value-First/Timing/Score)
- `nodes/acquisition/outbound_personalizer.py` — L1/L2/L3 + Timing連携
- `nodes/acquisition/inbound_magnet.py` — Always-On 3戦略
- `migrations/002_trust_engine.sql` — 4テーブル + RLS

---

## ✅ Sprint 3: Content & Campaign — 戦闘力 45/100

**完了: 2026-02-22 | Commit: `7324c5a` | テスト: 54/54**

- `nodes/acquisition/content_architect.py` — PASTOR/Challenger統合
- `nodes/acquisition/campaign_orchestrator.py` — マルチチャネル同期
- `nodes/acquisition/viral_engineer.py` — UGC + トレンドライド
- `nodes/acquisition/ad_optimizer.py` — 4プラットフォーム自律配分

---

## ✅ Sprint 4: Conversion Full — 戦闘力 60/100

**完了: 2026-02-23 | Commit: `ab02e99` | テスト: 69/69**

- **B2B**: nurture_sequencer → proposal_generator → meeting_setter → close_advisor
- **B2C**: activation_optimizer → retention_looper → monetization_trigger
- **C2C**: onboarding_sequencer → trust_builder → marketplace_growth_driver
- `conditional_edges`でconversion_mode動的ルーティング

---

## ✅ Sprint 5: Evolution + All 23 Nodes — 戦闘力 85/100

**完了: 2026-02-23 | Commit: `5a125cd` | テスト: 82/82**

- `nodes/evolution/performance_analyst.py` — B2B/B2C/C2C KPI + ヘルススコア
- `nodes/evolution/ab_optimizer.py` — 自動A/B + Intelligence再計算ループ
- `nodes/acquisition/community_seeder.py` — C2Cキーパーソン
- `nodes/acquisition/lead_qualifier.py` — MQL/SQL/Activated自動判定

---

## ✅ Sprint 6: PLG Launch API — 戦闘力 90/100

**完了: 2026-02-23 | Commit: `1a6b6e3` | テスト: 95/95**

- `server/tenant.py` — APIKey認証 + 4プラン制限
- `server/routes/growth.py` — 全パイプラインAPI
- `server/routes/tenants.py` — テナントCRUD
- `server/app.py` v1.0.0 — 4ルーター統合
- `migrations/003_plg_launch.sql` — tenants/api_keys/blueprints/runs/outcomes + RLS

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
> **現在地**: v1.0.0 — 全6スプリント完走
> **戦闘力**: 90/100
