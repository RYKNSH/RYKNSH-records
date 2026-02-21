# RYKNSH records Architecture Blueprint
> 限界費用ゼロの「全自動エンタメホールディングス」を支えるシステム基盤

---

## 1. 全体設計思想 (Core Philosophy)

「アーティスト以外全員AI」のモデルを成立させるため、システム全体は以下の3つの柱で構成される。

1. **Multi-Graph Orchestration (LangGraph)**
   単一の巨大AIではなく、各業務プロセス（制作、広報、検証など）を独立したGraphとしてモジュール化し、Mothership Agentがオーケストレーションする。
2. **Two-Tier State Management (Supabase)**
   AIの「記憶（State）」と「ビジネスデータ（Metadata）」をPostgreSQL上で分離統合する。
3. **Single Source of Truth (GitHub)**
   すべてのプロセス、アセット、意思決定の履歴をGitHubに集約し、それをトリガーとしてAIが自律稼働する。

---

## 2. アーキテクチャ図

```mermaid
graph TD
    %% Users
    Fan[Fan / User]
    Developer[Human Developer / Artist]

    %% Frontend
    subgraph Frontend["Studio Stream (Next.js / Vercel)"]
        UI[Process Observer UI & Community]
    end

    %% Database & State
    subgraph Storage["Supabase (PostgreSQL)"]
        DB[(Business Data / RAG Knowledge)]
        State[(LangGraph Checkpoint State)]
    end

    %% GitHub
    subgraph Repo["GitHub"]
        GH_Code[Source Code / Music Assets]
        GH_Actions[GitHub Actions / CI Webhooks]
    end

    %% Backend AI System
    subgraph HoldingSystem["RYKNSH Mothership (LangGraph)"]
        Orchestrator((Mothership Agent))
        
        subgraph Sub_Graphs["Subsidiary Graphs"]
            QA[①品質保証AI Graph]
            Prod[②制作会社 Graph]
            Growth[③グロース Graph]
            PR[④広報PR Graph]
        end
    end

    %% Connections
    Fan <-->|WebSockets (Realtime) / REST| UI
    UI <-->|Fetch Meta/State via RLS| Storage
    UI <-->|Fetch Commits/PRs| Repo
    
    Developer -->|Push/PR| Repo
    Repo -->|Webhook Trigger| GH_Actions
    GH_Actions -->|Invoke FastAPI/Webhook| HoldingSystem
    
    HoldingSystem <-->|Read/Write Checkpoints| State
    HoldingSystem <-->|Read/Write Meta & Vectors| DB
    
    Orchestrator -->|Dispatch Sub-tasks| QA
    Orchestrator -->|Dispatch Sub-tasks| PR
    Orchestrator -->|Dispatch Sub-tasks| Prod
    Orchestrator -->|Dispatch Sub-tasks| Growth
    
    Sub_Graphs -->|Commit / Automate PR / Merge| Repo
```

---

## 3. コンポーネント詳細

### 3.1 Orchestration Layer (LangGraph)
Mothership Agent（L0）が中央指揮を取り、各子会社の機能特化Graph（L1）を呼び出す階層構造。

- **Mothership Agent**: 楽曲のリリースや炎上検知などのトップレベルイベントを受け取り、「広報AIにプレスリリースを書かせる」「制作AIにジャケットを生成させる」といった指示を非同期にディスパッチする。
- **Subsidiary Graphs**: 個別の業務ロジックをカプセル化。例えば広報Graphは「リサーチ→ドラフト作成→レビュー→配信」という内部ステートマシンを持つ。
- **ヒューマンインザループ (Human-in-the-loop)**: LangGraphの `interrupt_before` を活用し、重要地点（リリース承認や大口決済）では人間のアーティストや経営陣の承認を待機する。

### 3.2 Data Layer (Supabase / PostgreSQL)
LangGraphとフロントエンドの橋渡しを行う強固なデータ基盤。

- **Checkpointer State**: `AsyncPostgresSaver` を用いて、全Agentのスレッド状態、会話履歴、内部変数を完全永続化。サーバーが再起動しても途中から再開可能。
- **Business Data**: 楽曲メタデータ、IPのパラメータ、生成されたアセットURL。
- **Realtime Subscription**: ファン向けUI（Studio Stream）はSupabaseを購読することで、AIが生成プロセスを進める様子をリアルタイムタイムラインとして観測できる。
- **Row Level Security (RLS)**: 
  - AIバックエンド: `Service Role Key` でフルアクセス。
  - フロントエンド(ファン): `Anon Key + JWT`。
  - アプリのAPIサーバーを書くことなく、「VIP課金フィルター」や「特定プロジェクトの閲覧権限」をPostgreSQLレイヤーで強固に制御。

### 3.3 Infrastructure & GitOps (GitHub)
- **SSOT (Single Source of Truth)**: 全てのアセット（音声データ、画像、コード）と歴史はGitHubリポジトリに保存。
- **自律的CI/CD**: 人間やAIがPull Requestを作成すると、GitHub Actionsがトリガーされ、品質保証AI（Velieモジュール）がコードやアセットのレビューを完全自動で行い、条件を満たせばマージする。

---

## 4. デプロイメント・スタック

| コンポーネント | 利用技術 | 選定理由 |
|--------------|----------|----------|
| **AI Backend** | Python, FastAPI, LangGraph | 最先端のマルチエージェント制御、ステートフルなワークフロー構築のデファクト |
| **Database** | Supabase (Postgres, pgvector) | RLSによる強力な直接アクセス制御、リアルタイム購読、ベクトル検索へのネイティブ対応 |
| **Frontend** | Next.js, Vercel | エッジでの高速描画（Edge Config）、グローバルアクセス最適化 |
| **Source Control**| GitHub, Actions | 開発者の参加ハードルをゼロにする世界共通のインフラ。Webhook連携の容易さ |
| **LLM Routing** | テックラボ製ルーター | Claude(長文/推論), GPT-4o(汎用), 独自モデルをタスクに応じて動的切り替え |

---

## 5. 次のステップ（実装要件）
このブループリントに基づき、最初の具現化である **「Phase 1: 品質保証AI（QA/検証エージェント事業）」** のCI/CDパイプラインとLangGraphベースのレビューエンジンの実装へと進む。

---
*Last Updated: 2026-02-21*
*Version: 1.0 (Blueprint V7)*
