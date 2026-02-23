# RYKNSH records — ROADMAP
> **本社（Mothership）視点のグランドロードマップ**

**Version**: 1.0
**Last Updated**: 2026-02-23
**Perspective**: CEO / Holdings HQ

---

## Overview

本ロードマップは WHITEPAPER.md §11（Execution Roadmap）を本社視点で具体化したものである。
本社の役割は **「ビジョン統括 / 法務・IP管理 / 経理 / 配信インフラ / HR・スカウト(L0) / Boundary Protocol の執行」** であり、各子会社の自律稼働のための環境整備と、グループ全体のシナジー最大化を担う。

---

## Grand Roadmap（4 Phase構成）

```
Phase 0     Phase 0.5       Phase 1          Phase 2          Phase 3          Phase 4
TODAY    → M0（基盤設計）→ M1（The Core）→ M2（Engine）  → M3（Defense）  → M4〜（Final Show）
本社固定    SOTA/Scaffold   Velie + Ada      Lumina + Cyrus   Noah + Iris      Label 01
                                ↑現在地
```

---

### Phase 0: Architecture Lock（完了）

**目的**: ホールディングスの全体設計を確定させる

| 成果物 | 状態 |
|--------|------|
| ディベート（Round 1-19） | ✅ 完了 |
| Strategy Bible v2 | ✅ 完了 |
| Architecture Blueprint v1.1 | ✅ 完了 |
| Master Execution Plan v1.3 | ✅ 完了 |
| Company Directory v1.2 | ✅ 完了 |
| WHITEPAPER v1.0 | ✅ 完了 |
| 本社 ROADMAP（本文書）| ✅ 完了 |

---

### Phase 0.5: SOTA Research & Scaffolding（部分完了）

**目的**: 開発に入る前に境界管理を物理固定し、最新技術で武装する

| 成果物 | 状態 |
|--------|------|
| Monorepoスケルトン（全7子会社の空ディレクトリ） | ✅ 完了 |
| 各子会社 README.md / WHITEPAPER.md | 🔶 一部完了（Velie/Ada/Lumina/Cyrus） |
| SOTA Research（LangGraph/Supabase最新機能調査）| 🔶 部分的 |
| Local Skill Audit（既存スキル群の査定）| ⬜ 未着手 |

---

### Phase 1: The Core Foundation（進行中）
> **M1 — Velie（QA）+ Ada（AI R&D）**

**目的**: 全社の品質基盤（Velie）と頭脳基盤（Ada）を完成させ、以降の開発を加速するDogfoodingエンジンを確立する

| 子会社 | 現状 | Phase 1完了条件 |
|--------|------|----------------|
| ① Velie | Sprint 1 Core Done | Sprint 4完了（Stripe課金付きSaaSダッシュボード + OSS公開） |
| ⑤ Ada | Sprint 1 Core Done | Core API完成 + マルチプロバイダーLLMルーティング + 外販API公開 |

**本社の責務（Phase 1）**:
- Golden Template（SaaS共通基盤）の品質検証と承認
- Velie CI のグループ全社CI/CD統合の指揮
- Ada Core API のマルチテナント設計レビュー
- 内販移転価格ルールの初版策定
- Phase 2移行判断のGo/No-Go

---

### Phase 2: The Creative & Growth Engine
> **M2 — Lumina（制作）+ Cyrus（グロース）**

**目的**: Golden Templateを流用し、クリエイティブアセット供給とマーケティング自動化を稼働させる

| 子会社 | 現状 | Phase 2完了条件 |
|--------|------|----------------|
| ② Lumina | Whitepaper v2 Done | AI Creative Studio + MV Factory 稼働 + 外販開始 |
| ③ Cyrus | Whitepaper v2 Done | Growth Agent + Campaign Engine 稼働 + 外販開始 |

**本社の責務（Phase 2）**:
- Golden Template のLumina/Cyrusへの転用承認
- 制作→グロースの循環フロー（内販）の設計・接続
- 外販プライシングの最終承認
- Phase 3移行判断のGo/No-Go

---

### Phase 3: The Community & Defense
> **M3 — Noah（コミュニティ）+ Iris（広報PR）**

**目的**: ファン課金基盤とブランド防衛体制を構築し、Label 01稼働の前提条件を整える

| 子会社 | 現状 | Phase 3完了条件 |
|--------|------|----------------|
| ⑥ Noah | Not Started | Fan Platform MVP + 課金エンジン + コミュニティUI |
| ④ Iris | Not Started | AI Press Agent + Crisis Shield 24h監視 |

**本社の責務（Phase 3）**:
- Noah課金エンジンと Stripe 統合の法務レビュー
- Iris広報ポリシーの策定（グループ統一ガイドライン）
- 全6社の内販フロー統合テスト指揮
- Label 01 開始判断のGo/No-Go

---

### Phase 4: The Final Show
> **M4〜 — Label 01（音楽レーベル）**

**目的**: 6つの自律型SaaSを駆使し、原価ほぼゼロでフラッグシップIPをリリース

| 子会社 | Phase 4完了条件 |
|--------|----------------|
| ⑦ Label 01 | 初代IP のリリース + Mad Editor Protocol 稼働 + ファン課金開始 |

**本社の責務（Phase 4）**:
- Mad Editor Agent のパラメータ設計・倫理ガイドライン策定
- 全社エコシステム（①〜⑥）の統合運用監視
- L0 オーディション層の設計と開放
- Cross-Maison Collaboration Engine の設計
- Mothership Agent（L0 Orchestrator Graph）の実装指揮

---

## 本社 固有ロードマップ（Phase横断）

本社は子会社とは異なり、**全Phaseを横断して継続的に稼働**する。

```
Phase 0   Phase 0.5   Phase 1   Phase 2   Phase 3   Phase 4
  ├─ ビジョン固定 ──────────────────────────────────────────→
  ├─ Boundary Protocol ────────────────────────────────────→
  ├─ 法務・契約 ───────────────────────────────────────────→
  ├─ 経理・移転価格 ────────────────── ──────────────────────→
  │              ├─ Golden Template承認 ─→
  │              │       ├─ 内販フロー接続 ────→
  │              │       │       ├─ 全社統合テスト ─→
  │              │       │       │        ├─ Mothership Agent ─→
  └──────────────┴───────┴───────┴────────┴──────────────────→
```

---

*See also: [WHITEPAPER.md](file:///Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH%20records/docs/WHITEPAPER.md) | [MILESTONES.md](file:///Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH%20records/docs/MILESTONES.md)*
