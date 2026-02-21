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
4. **True Multi-Tenancy (Inbound/Outbound Integration)**
   「内販（自社レーベル利用）」と「外販（SaaS顧客利用）」を分けない。全リクエストを単一のインフラ上で、SupabaseのRLSとLangGraphのConfigによって完全に分離・スケールさせる。
5. **The Boundary Protocol (境界管理の絶対ルール)**
   開発・デバッグ時において、担当ディレクトリ外のコード修正や、システム全体を動かしてのテストをシステム上・プロンプト上で固く禁じる。被害の波及（カスケーディング障害）を最小化する。

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
            QA[① Velie Graph]
            Prod[② Lumina Graph]
            Growth[③ Syndicate Graph]
            PR[④ Vanguard Graph]
        end
    end

    %% Connections
    Fan <-->|WebSockets (Realtime) / REST| UI
    SaaS_Customer[SaaS Customer] -->|Push/PR / API| Repo
    UI <-->|Fetch Meta/State via RLS| Storage
    UI <-->|Fetch Commits/PRs| Repo
    
    Developer -->|Push/PR| Repo
    Repo -->|Webhook Trigger| GH_Actions
    GH_Actions -->|Enqueue Event| MsgQueue
    
    subgraph Async_Queue["Serverless Queue Layer"]
        MsgQueue[[Message Queue (Redis/SQS)]]
    end
    
    MsgQueue -->|De-queue| HoldingSystem
    
    HoldingSystem <-->|Read/Write Checkpoints (Tenant Scoped)| State
    HoldingSystem <-->|Read/Write Meta & Vectors (Tenant Scoped)| DB
    
    Orchestrator -->|Dispatch Sub-tasks| QA
    Orchestrator -->|Dispatch Sub-tasks| PR
    Orchestrator -->|Dispatch Sub-tasks| Prod
    Orchestrator -->|Dispatch Sub-tasks| Growth
    
    Sub_Graphs -->|Commit / Automate PR / Merge| Repo
```

---

## 3. コンポーネント詳細

### 3.1 Orchestration & Agent Layer (LangGraph)
Mothership Agent（L0）が中央指揮を取り、各子会社の機能特化Graph（L1）を呼び出す階層構造。

-   **Multi-Tenant Injection**: 全テナント（自社レーベルや外部SaaS顧客）は全く同じAgentコードを実行するが、呼び出し時に `RunnableConfig` で `tenant_id` を注入し、システムプロンプト（人格）やLLMプロバイダを動的に切り替える。
-   **Mothership Agent**: 楽曲のリリースや炎上検知などのトップレベルイベントを受け取って処理。
-   **ヒューマンインザループ**: LangGraphの `interrupt_before` を活用し、重要地点（リリース承認や大口決済）では人間の承認を待機する。

### 3.2 Data Layer (Supabase / PostgreSQL)
LangGraphとフロントエンドの橋渡しを行う強固なデータ基盤とマルチテナンシーの核。

-   **Row Level Security (RLS)**: 
    「内販（RYKNSH）」も「外販顧客A社」も同じテーブルに入る。RLSによって、JWTトークン内の `tenant_id` に紐づくデータ以外はPostgreSQLレベルで不可視化される。専用のAPIサーバーを書く必要がなく、強固なDBレベルの分離を実現する。
-   **Checkpointer State**: `AsyncPostgresSaver` を用いて全Agentのスレッド状態を永続化。
-   **Business Data**: 楽曲メタデータ、IPのパラメータ、S3 URL。
-   **Realtime Subscription**: ファン向け観測UI「Studio Stream」のバックエンドとして、AI同士の議論をリアルタイム配信。

### 3.3 Infrastructure & GitOps (GitHub + Message Queue)
-   **SSOT**: 全てのアセット（コード、動画、音声）のマスターはGitHub。
-   **自律的CI/CD**: GitHub Actionsがトリガーされ、完了を待たずに非同期キュー（Message Queue）にリクエストを投げる。
-   **Serverless Worker Scaling**: Queueに溜まったリクエストを数百台のワーカーが非同期で処理（LangGraph実行）するため、リクエストがバーストしてもシステムは決して落ちない。限界費用ゼロの無限スケールを実現する。

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
*Version: 1.1 (Scale Blueprint V8)*
