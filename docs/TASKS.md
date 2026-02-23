# RYKNSH records — TASKS
> **本社（Mothership）視点の実行タスクリスト**

**Version**: 1.0
**Last Updated**: 2026-02-23
**Perspective**: CEO / Holdings HQ

---

## タスク体系

各マイルストーンを、**1セッション（数時間）以内に完了可能な粒度**のタスクに分解する。
タスクIDは `マイルストーンID-連番` で命名（例: `HQ005-01`）。

> **凡例**: ✅ 完了 / 🔶 進行中 / ⬜ 未着手

---

## Phase 0.5: SOTA Research & Scaffolding

---

### HQ-005: 全子会社ホワイトペーパーの完備

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ005-01 | Iris ホワイトペーパー作成 | ⬜ | 本社 | 広報/PR/炎上監視の事業設計 |
| HQ005-02 | Noah ホワイトペーパー作成 | ⬜ | 本社 | コミュニティPF/課金基盤の事業設計 |
| HQ005-03 | Label 01 ホワイトペーパー作成 | ⬜ | 本社 | 音楽レーベル/Mad Editor/IP育成の事業設計 |

---

### HQ-006: SOTA Research 完了

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ006-01 | LangGraph 最新機能調査 | ⬜ | 本社/Ada | `Command`, `interrupt`, `AsyncPostgresSaver` 最新挙動 |
| HQ006-02 | Supabase RLS 最適パターン調査 | ⬜ | 本社/Ada | マルチテナント設計のベストプラクティス |
| HQ006-03 | Next.js 15+ 最適化調査 | ⬜ | 本社 | Edge Config, App Router, Server Actions |
| HQ006-04 | MCP サーバー最新調査 | ⬜ | 本社/Ada | GitHub MCP, Supabase MCP の能力査定 |
| HQ006-05 | Local Skill Audit（既存スキル群の査定） | ⬜ | 本社 | `skills/` 12件の RYKNSH 転用可能性 |
| HQ006-06 | Architecture Blueprint への反映 | ⬜ | 本社 | 調査結果を `architecture_blueprint.md` v2 に統合 |

---

### HQ-007: Boundary Protocol のガバナンス文書化

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ007-01 | `BOUNDARY_PROTOCOL.md` 独立文書作成 | ⬜ | 本社 | WHITEPAPER §12 を拡張。具体例・違反時の対処を追記 |
| HQ007-02 | 各子会社 README に Boundary Protocol リンク追加 | ⬜ | 本社 | 全子会社の README に参照セクション |

---

## Phase 1: The Core Foundation

---

### INT-001: Velie — 外販SaaS完成

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT001-01 | Sprint 2: Supabase `tenant_id` + RLS 実装 | ⬜ | Velie | マルチテナント分離 |
| INT001-02 | Sprint 2: LangGraph Checkpointer → Supabase接続 | ⬜ | Velie | Stateful化（過去レビュー記憶） |
| INT001-03 | Sprint 2: RunnableConfig テナント別プロンプト注入 | ⬜ | Velie | 人格の動的切り替え |
| INT001-04 | Sprint 3: Webhook → Message Queue 分離 | ⬜ | Velie | Redis/SQS 導入 |
| INT001-05 | Sprint 3: Worker Pool の自動スケール設定 | ⬜ | Velie | 非同期ワーカー化 |
| INT001-06 | Sprint 4: Next.js ダッシュボード構築 | ⬜ | Velie | レビュー履歴・API使用量閲覧 |
| INT001-07 | Sprint 4: Stripe サブスク/従量課金統合 | ⬜ | Velie | 外販課金インフラ |
| INT001-08 | Sprint 4: OSS公開（Public Repo無料レビュー） | ⬜ | Velie | Product Hunt ローンチ準備 |

---

### INT-002: Ada — Core API 外販完成

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT002-01 | マルチプロバイダーLLMルーティング完成 | 🔶 | Ada | Claude/GPT-4o 動的切り替え |
| INT002-02 | テナント別 LLM 設定 API | ⬜ | Ada | テナントごとにモデル選択 |
| INT002-03 | ストリーミングレスポンス（SSE）最適化 | ✅ | Ada | 完了済み |
| INT002-04 | レート制限 | ✅ | Ada | 完了済み |
| INT002-05 | Ada Core API ドキュメント + OSS公開 | ⬜ | Ada | Agent Framework として |
| INT002-06 | Fine-tune Lab Prototype | ⬜ | Ada | 業界特化型LLMファインチューニング |

---

### HQ-008: Golden Template の確立と承認

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ008-01 | Velie SaaS基盤のコンポーネント一覧化 | ⬜ | 本社 | Webhook/Queue/Supabase/Stripe/Next.js |
| HQ008-02 | Template リポジトリの作成 | ⬜ | 本社 | 汎用化したボイラープレート |
| HQ008-03 | Lumina/Cyrus への転用シミュレーション | ⬜ | 本社 | 差分の特定と文書化 |
| HQ008-04 | 正式承認（Go/No-Go） | ⬜ | CEO | Golden Template として確定 |

---

### HQ-009: グループ全社 CI/CD 統合

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ009-01 | Velie CI GitHub App の設定 | ⬜ | Velie/本社 | グループ全リポジトリへのインストール |
| HQ009-02 | 全子会社 CI パイプライン統一設定 | ⬜ | 本社 | `.github/workflows/` テンプレート |
| HQ009-03 | 品質ゲートのmerge保護ルール設定 | ⬜ | 本社 | GitHub Branch Protection |
| HQ009-04 | CI通過率モニタリングダッシュボード | ⬜ | 本社/Velie | 99%+ 目標 |

---

### HQ-010: 内販移転価格ルール初版

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ010-01 | 内販サービス定義（何を誰がいくらで提供するか） | ⬜ | 本社/CFO | Velie QA / Ada LLM / Lumina アセット 等 |
| HQ010-02 | Supabase 利用量集計クエリ設計 | ⬜ | 本社/Ada | 全テナント当月APIコール集計SQL |
| HQ010-03 | 月次内販レポート自動生成フロー | ⬜ | 本社 | 各社の内販利用料を自動算出 |

---

### HQ-011: Phase 2 移行判断

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ011-01 | Go/No-Go チェックリスト作成 | ⬜ | 本社 | INT-001, INT-002, HQ-008, HQ-009 の完了確認 |
| HQ011-02 | CEO 最終承認 | ⬜ | CEO | Phase 2 正式開始 |

---

## Phase 2: The Creative & Growth Engine

---

### INT-003: Lumina — AI Creative Studio 外販開始

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT003-01 | Golden Template からの基盤コピー | ⬜ | Lumina | HQ-008 完了後 |
| INT003-02 | 画像生成パイプライン実装 | ⬜ | Lumina | Nodeの設計（LangGraph） |
| INT003-03 | 動画生成パイプライン実装 | ⬜ | Lumina | MV Factory |
| INT003-04 | アセットサブスクリプション基盤 | ⬜ | Lumina | 月額素材サービス |
| INT003-05 | 外販ダッシュボード + Stripe | ⬜ | Lumina | Golden Template流用 |
| INT003-06 | OSS公開 / Product Hunt | ⬜ | Lumina | |

---

### INT-004: Cyrus — Growth Agent 外販開始

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT004-01 | Golden Template からの基盤コピー | ⬜ | Cyrus | |
| INT004-02 | リード獲得→ナーチャリング Graph 実装 | ⬜ | Cyrus | Growth Agent |
| INT004-03 | SNS広告 Campaign Engine 実装 | ⬜ | Cyrus | A/Bテスト自動化 |
| INT004-04 | Insight API（トレンド分析）実装 | ⬜ | Cyrus | 従量課金 |
| INT004-05 | 外販ダッシュボード + Stripe | ⬜ | Cyrus | |
| INT004-06 | イベント部門のプロトタイプ | ⬜ | Cyrus | グロース社内チーム |

---

### HQ-012: 内販循環フローの接続

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ012-01 | Lumina→Cyrus 内販API接続設計 | ⬜ | 本社 | アセット→配信の自動フロー |
| HQ012-02 | Cyrus→Velie 品質検証フロー接続 | ⬜ | 本社 | 配信物のQA |
| HQ012-03 | E2Eシミュレーション（架空キャンペーン） | ⬜ | 本社 | 内販循環の実証 |

---

### HQ-013: 外販プライシング最終承認

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ013-01 | 4社（Velie/Ada/Lumina/Cyrus）価格表確定 | ⬜ | 本社/CFO | |
| HQ013-02 | Stripe プラン設定 | ⬜ | 本社 | 各社のサブスク/従量課金 |

---

## Phase 3: The Community & Defense

---

### INT-005: Noah — Fan Platform MVP

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT005-01 | Noah ホワイトペーパーからの実装設計 | ⬜ | Noah | HQ005-02 完了後 |
| INT005-02 | Golden Template コピー + コミュニティUI | ⬜ | Noah | |
| INT005-03 | 課金エンジン（サブスク/チップ/トークン） | ⬜ | Noah | PF手数料15-20% |
| INT005-04 | Issue/PR ビューワ（Studio Stream MVP） | ⬜ | Noah | Git → ファン向けUI変換 |
| INT005-05 | Community Analytics ダッシュボード | ⬜ | Noah | エンゲージメント/チャーン予測 |

---

### INT-006: Iris — AI Press Agent + Crisis Shield

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT006-01 | Iris ホワイトペーパーからの実装設計 | ⬜ | Iris | HQ005-01 完了後 |
| INT006-02 | Golden Template コピー + PR自動執筆 | ⬜ | Iris | AI Press Agent |
| INT006-03 | メディアリスト選定→配信→追跡 | ⬜ | Iris | |
| INT006-04 | Crisis Shield 24h SNS/ニュース監視 | ⬜ | Iris | 炎上即時検知 |
| INT006-05 | 対応ドラフト自動生成 + エスカレーション | ⬜ | Iris | |
| INT006-06 | Brand Audit（ブランドイメージ定量分析） | ⬜ | Iris | |

---

### HQ-015〜018: 本社 Phase 3 タスク

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| HQ015-01 | ファン向けサブスク利用規約作成 | ⬜ | 本社 | 法務 |
| HQ015-02 | 特商法表記 + プライバシーポリシー | ⬜ | 本社 | 法務 |
| HQ016-01 | グループ広報ガイドライン文書作成 | ⬜ | 本社 | Iris遵守基準 |
| HQ016-02 | 危機管理マニュアル作成 | ⬜ | 本社 | エスカレーションフロー |
| HQ017-01 | 架空IPによる全6社E2Eシミュレーション設計 | ⬜ | 本社 | |
| HQ017-02 | シミュレーション実行 + 結果検証 | ⬜ | 本社 | |
| HQ018-01 | Label 01 Go/No-Go チェックリスト | ⬜ | 本社 | |
| HQ018-02 | CEO 最終承認 | ⬜ | CEO | |

---

## Phase 4: The Final Show

---

### INT-007 + HQ-019〜022: Label 01 & Mothership

| ID | タスク | 状態 | 担当 | 備考 |
|----|--------|------|------|------|
| INT007-01 | 初代IP アーティスト選定基準策定 | ⬜ | 本社/Label01 | |
| INT007-02 | Mad Editor Agent V1 実装 | ⬜ | Label01/Ada | |
| INT007-03 | Studio Stream 制作過程公開UI | ⬜ | Label01/Noah | |
| INT007-04 | ファン課金フロー（Process Pass / VIP Branch） | ⬜ | Label01/Noah | |
| HQ019-01 | Predictability Score 閾値設計 | ⬜ | 本社 | |
| HQ019-02 | 制約生成アルゴリズム設計 | ⬜ | 本社/Ada | |
| HQ019-03 | インセンティブ設計（特権アンロック条件） | ⬜ | 本社 | |
| HQ019-04 | 倫理レビュー（アーティスト負荷検証） | ⬜ | 本社 | |
| HQ020-01 | L0 Audition Layer 設計 | ⬜ | 本社 | |
| HQ020-02 | 軽量共用AI スクリーニングBot | ⬜ | 本社/Ada | |
| HQ020-03 | L0→L1 昇格基準定義 | ⬜ | 本社 | |
| HQ021-01 | Mothership Agent Graph 設計 | ⬜ | 本社/Ada | L0 Orchestrator |
| HQ021-02 | イベントルーティング + 並列ディスパッチ実装 | ⬜ | 本社/Ada | |
| HQ021-03 | 完了集約 + エラーハンドリング | ⬜ | 本社/Ada | |
| HQ022-01 | Cross-Maison マッチングアルゴリズム設計 | ⬜ | 本社 | |
| HQ022-02 | コラボリポジトリ自動生成機能 | ⬜ | 本社/Ada | |

---

## 📊 Phase別タスクサマリー

| Phase | 本社(HQ)タスク | 統合(INT)タスク | 合計 | 完了 | 残 |
|-------|--------------|---------------|------|------|-----|
| 0 | 3 MS / 0 tasks | — | — | ✅ ALL | 0 |
| 0.5 | 4 MS / 11 tasks | — | 11 | 0 | 11 |
| 1 | 4 MS / 13 tasks | 2 MS / 14 tasks | 27 | 2 | 25 |
| 2 | 3 MS / 5 tasks | 2 MS / 12 tasks | 17 | 0 | 17 |
| 3 | 4 MS / 8 tasks | 2 MS / 11 tasks | 19 | 0 | 19 |
| 4 | 4 MS / 12 tasks | 1 MS / 4 tasks | 16 | 0 | 16 |
| **Total** | **18 MS / 49 tasks** | **7 MS / 41 tasks** | **90** | **2** | **88** |

---

## 🎯 今すぐ着手可能なタスク（No Dependencies）

以下は依存関係が解消済みで、**今日始められる**タスク：

1. **HQ005-01**: Iris ホワイトペーパー作成
2. **HQ005-02**: Noah ホワイトペーパー作成
3. **HQ005-03**: Label 01 ホワイトペーパー作成
4. **HQ006-01〜05**: SOTA Research（並列実行可能）
5. **HQ007-01**: Boundary Protocol 独立文書化
6. **INT001-01〜03**: Velie Sprint 2（進行可能）
7. **INT002-01〜02**: Ada テナント別LLM設定

---

*See also: [ROADMAP.md](file:///Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH%20records/docs/ROADMAP.md) | [MILESTONES.md](file:///Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH%20records/docs/MILESTONES.md) | [WHITEPAPER.md](file:///Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH%20records/docs/WHITEPAPER.md)*
