# Ada Whitepaper: The AI Lifecycle Platform

> **このドキュメントは Ada 開発の北極星である。**
> - 開発セッション開始時に必ず参照すること
> - 方向性に迷ったときに立ち返ること
> - 全ての設計判断はこのドキュメントに基づくこと

---

## 1. Adaとは何か

**「AI思考のライフサイクルを管理するプラットフォーム」**

AdaはLLMプロキシではない。エージェントフレームワークでもない。
Adaは **「ゴール理解 → SOTA研究 → ディベート → 重み付け設計 → 実装 → 検証 → 自律強化学習」** という
AI思考の全工程を最高品質で回すプラットフォームだ。

**鎧制師が自分の鎧を自分で作る。** Ada自身がAdaのLifecycleを使って新しいエージェントを設計できる。

### 差別化ポイント

Adaの真の競争力は「3-Layer構造」そのものではない。以下の2つだ：

1. **再帰的自己設計**: AdaがAdaのLifecycleを使って新しいエージェントを設計する。ツールがツールを鍛える。セキュリティエージェントもQAエージェントもAda自身が設計する。
2. **6社の実戦検証**: RYKNSH傘下6社（Velie/Lumina/Cyrus/Iris/Noah/Label 01）で実際に商用プロダクトを運用した結果から生まれるテンプレート。他のフレームワーク提供者は自分ではプロダクトを作っていない。


## 2. 3-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  🔵 LIFECYCLE — 何を作るか（設計時1回）             │
│  goal_intake → researcher[並列] → debater →      │
│  architect → scribe                              │
├─────────────────────────────────────────────────┤
│  🟢 EXECUTION — 実際に作る（毎リクエスト）           │
│  sentinel ││ context_loader → strategist →       │
│  executor[並列Fan-out] → aggregator →            │
│  validator → formatter                           │
├─────────────────────────────────────────────────┤
│  🔴 EVOLUTION — 自律強化（定期バッチ）              │
│  tester → evolver → (feedback → Lifecycle)       │
├─────────────────────────────────────────────────┤
│  🛡️ SECURITY — 横断的セキュリティ（全レイヤー）     │
│  自製可能・外部APIも利用可                          │
└─────────────────────────────────────────────────┘
```

### 各レイヤーの動作頻度

| レイヤー | 頻度 | 機能 |
|---------|------|------|
| 🔵 Lifecycle | 設計時に1回 | ゴール理解→リサーチ→ディベート→設計→永続化。結果はAgentBlueprintとしてExecution configに焼き込まれる |
| 🟢 Execution | 毎リクエスト | sentinel → formatter。高速パイプライン |
| 🔴 Evolution | 日次/週次 | フィードバック収集→パラメータ自動調整。Lifecycleにフィードバック |

### Lifecycle自律度レベル

| Level | 時期 | 動作 |
|-------|------|------|
| **L1** | 現在〜M3 | 人間がトリガー → Adaが実行 → 人間が承認 |
| **L2** | M4〜 | Adaが自律トリガー → 人間が承認（Human-in-the-loop） |
| **L3** | M6〜 | 完全自律（evolverがLifecycleを自動起動し、設計改善を提案） |

### リソース管理

並列実行時のテナント間資源分離:
- リクエスト単位のレートリミット（既存）に加え、**ノード実行単位の制御**を実装
- テナントAの並列executorがテナントBのリソースを圧迫しない


## 3. 全14ノード

### 🔵 Lifecycle Layer（設計時1回）

| ノード | 機能 |
|-------|------|
| `goal_intake` | ゴールと前提を超深いレベルで理解。不明点はHuman-in-the-loopでインタビュー。理解度100%になるまで進まない |
| `researcher` | SOTA論文・ベストプラクティスを並列検索（Web検索Tool + RAG + 論文DB）。信頼性スコア付き |
| `debater` | ゴールに最適なペルソナを自動選出。全員合致の最適解が出るまで何ラウンドでも繰り返す |
| `architect` | 最適解を重み付け（品質 > 効率 > 速度 > 軽量）。ツール・MCP・API・スキル・ナレッジ・WFを徹底リサーチして選定 |
| `scribe` | AgentBlueprint + ロードマップ + マイルストーンを作成し永続化。コンテキストを忘れない仕組み |

### 🟢 Execution Layer（毎リクエスト）

| ノード | 機能 |
|-------|------|
| `sentinel` | 入力の安全性検証。Prompt Injection検出、有害コンテンツフィルタ、コード脆弱性スキャン。全リクエストの門番 |
| `context_loader` | テナント別コンテキスト注入。System Prompt + RAG検索 + ドキュメント参照 |
| `strategist` | 最適な思考戦略の選択。モデル・CoT・温度をPriority Weightsに基づいて動的決定 |
| `executor` | LLM呼び出し + ReActツールループ。並列Fan-out対応（複数視点同時分析） |
| `aggregator` | 並列executorの結果を統合。重み付き統合・矛盾検出・最終回答の合成 |
| `validator` | 出力の品質検証。幻覚チェック（Grounding）、フォーマット検証、トーン一貫性チェック |
| `formatter` | 結果の整形。OpenAI互換レスポンス構築、メタデータ付与、使用量計算 |

### 🔴 Evolution Layer（日次/週次）

| ノード | 機能 |
|-------|------|
| `tester` | 本番環境でのメトリクス収集。成功率・レイテンシ・ユーザー満足度 |
| `evolver` | フィードバックデータからパラメータ・プロンプトを自動調整。学習結果をLifecycleにフィードバック |

### 🛡️ Security（横断的）

Securityは1つのノードではない。全レイヤーを貫通する骨格：

- 🔵 `researcher`: 信頼性の低いソースのフィルタリング
- 🟢 `sentinel`: 入力のPrompt Injection検出（メインゲート）
- 🟢 `executor`: Tool実行時のサンドボックス + 出力サニタイズ
- 🟢 `validator`: 出力に含まれるコードの脆弱性スキャン
- 🔴 `evolver`: 学習データの汚染検出（Data Poisoning防止）

**外部セキュリティAPI（Claude Security等）は内部で利用可能だが、外販では打ち出さない。
Adaの3-Layer自体が「セキュリティエージェントを設計する」Lifecycleを回せるため。**


## 4. Priority Weights（全ノード共通設計原則）

```
🏆 最高品質 (0.40) > ⚡ 最大効率 (0.30) > 🚀 最高速度 (0.20) > 🪶 最軽量 (0.10)
```

品質のために速度を犠牲にすることはある。**速度のために品質を犠牲にすることは絶対にない。**

`strategist`ノードがこの重みに基づいてリクエストごとに最適な戦略を選択する。


## 5. 並列実行パターン

### Execution Layer — Fan-out/Fan-in

1つのタスクを複数のexecutorノードセットで同時並列処理：

```
strategist
    │
    ├── executor_A (コード品質分析)
    ├── executor_B (セキュリティ分析)    ← 同時並列
    ├── executor_C (パフォーマンス分析)
    │
aggregator (重み付き結果統合 + 矛盾解決)
    │
validator → formatter
```

**適用例:**
- Velie: 1つのPRを3視点で同時レビュー
- Cyrus: 集客・マーケティング・クリエイティブ・開発を並列実行
- Label 01: 音楽レビューを技術面・芸術面・マーケット面で同時分析

### Lifecycle Layer — 並列リサーチ

```
goal_intake
    │
    ├── researcher (技術論文)
    ├── researcher (競合分析)     ← 同時並列
    ├── researcher (ベストプラクティス)
    │
debater → architect → scribe
```

LangGraphの `Send()` API でネイティブに実装可能。


## 6. AgentBlueprint（Lifecycle → Execution接続）

scribeが出力する**AgentBlueprint**は、Lifecycle Layerの設計結果をExecution Layerに焼き込むインターフェース：

```json
{
  "blueprint_id": "velie-code-reviewer-v1",
  "quality_tier": "full",
  "system_prompt": "You are a senior code reviewer...",
  "tools": ["github_diff", "test_runner", "security_scan"],
  "model_preference": {
    "primary": "claude-sonnet-4",
    "fallback": "gpt-4o"
  },
  "parallel_executors": [
    {"name": "code_quality", "prompt": "...", "weight": 0.5},
    {"name": "security", "prompt": "...", "weight": 0.3},
    {"name": "performance", "prompt": "...", "weight": 0.2}
  ],
  "validation_rules": ["no_hallucination", "tone_consistency"],
  "rag_config": {
    "collections": ["strategy_bible", "past_reviews"],
    "relevance_threshold": 0.75
  }
}
```

- 永続化先: Supabase `ada_blueprints` テーブル（テナント別RLS）
- Execution Layerの`RunnableConfig`に自動注入
- バージョニング: Blueprint更新時に自動でv1, v2...と管理


## 7. 品質ティア

| ティア | パス | 並列実行 | 用途 |
|-------|------|---------|------|
| **Light** | strategist → executor → formatter | ❌ 不可 | リアルタイムチャット |
| **Standard** | sentinel → context_loader → strategist → executor → formatter | ⚠️ オプション | 一般的な業務 |
| **Full** | 全ノード通過（aggregator含む） | ✅ Fan-out/Fan-in | QA・セキュリティ |

テナント/子会社がAgentBlueprintの `quality_tier` で選択。
Standard + 並列実行のオプション有効化はBlueprintの`parallel_executors`設定による。


## 8. Evolution Layer — フィードバックメカニズム

### フィードバックソース

| 種類 | ソース | 収集方法 |
|------|-------|---------|
| **明示的** | ユーザーの👍/👎 + **コメント選択肢**（「的外れ」「冗長」「不正確」「トーンが違う」等）+ 自由記述 | APIレスポンスへの評価エンドポイント |
| **暗黙的** | レスポンスの採用率、再生成リクエスト、セッション離脱率 | testerが自動計測 |
| **品質メトリクス** | validator通過率、幻覚検出率、ツール実行成功率 | validatorが自動記録 |

### 調整対象

| 対象 | 調整方法 | 自律度Level |
|------|---------|------------|
| strategistのモデル選択テーブル | 成功率ベースの重み付け更新 | L1（M3〜） |
| context_loaderのRAG検索パラメータ | 関連性スコア閾値の最適化 | L1（M3〜） |
| executor用プロンプトテンプレート | 成功パターンの強化・失敗パターンの抑制 | L2（M4〜） |
| AgentBlueprint全体の再設計 | evolverがLifecycleを自動起動 | L3（M6〜） |

### 手法

- **M3**: 統計的最適化（成功率/採用率ベースのパラメータ調整）
- **M6**: 強化学習（十分なデータ蓄積後、Reward = ユーザー採用率 × validator通過率）


## 9. Boundary Protocol

```
Ada     = ノードパターン（型）を提供    → 鍛冶の型
子会社  = ツールとプロンプト（素材）を提供 → 型に流し込む鉄
外部顧客 = テンプレートを購入して自社Graphを構築 → 型を買って自分の刀を打つ
```

- Ada → 子会社の方向にデータが流れることはない（Pull型のみ）
- 子会社の業務ロジックにAdaは踏み込まない
- AdaはPassive Infrastructure: 呼ばれたら応え、呼ばれなければ沈黙する


## 10. 外販戦略

### 価格モデル（ハイブリッド: Usage + Outcome）

| Tier | 価格 | 内容 |
|------|------|------|
| **Free** | $0（月100ノード実行まで） | Execution Layer基盤 + 基本セキュリティ |
| **Usage** | $0.01-0.05 / ノード実行 | 使った分だけ。全ノードアクセス |
| **Lifecycle** | $99 / 設計1回 | Lifecycle Layer 1回実行 → AgentBlueprint納品 |
| **Enterprise** | 月額ベース + 成果報酬 | 実戦検証済みテンプレート + 成果連動（例: 採用率×単価） |

### 本丸: 検証済みノード = 天才の頭脳販売

**Adaの外販の本質は「検証済みノード自体の販売」。** いろんな業界の、いろんな役割を、世界最上位の天才たちの頭脳として購入して導入できる。

- 「世界最高のコードレビュアー」の頭脳 → Velieで検証済みのExecutionノードセット
- 「世界最高のグロースハッカー」の頭脳 → Cyrusで検証済みのExecutionノードセット
- 「世界最高のクリエイティブディレクター」の頭脳 → Luminaで検証済みのExecutionノードセット

**テンプレートは設計図に過ぎない。本当に売るのは「鍛え上げた刀そのもの」。** 各ノードに焼き込まれたプロンプト・モデル選択・RAGナレッジ・検証ルール——これが「天才の頭脳」の正体。

> 2026年のAIエージェント市場は成果報酬型（Outcome-Based）が主流。
> 月額固定サブスクは旧世代。AdaはUsage + Outcomeのハイブリッドで次世代を取る。


## 11. 技術スタック

| 領域 | 技術 |
|------|------|
| グラフエンジン | LangGraph |
| LLMプロバイダー | Anthropic Claude / OpenAI GPT |
| ベクトルDB | Supabase pgvector |
| API | FastAPI (OpenAI互換) |
| 状態管理 | LangGraph AsyncPostgresSaver |
| キュー | Redis Streams / In-memory fallback |
| テスト | pytest + pytest-asyncio |
| 並列実行 | LangGraph Send() API |

### 抽象化方針

全ノードはLangGraphのNode APIに直接依存せず、**AdaのNode Interface（AdaTool / AdaNode基底クラス）を経由する**。
これにより、将来的にグラフエンジンを交換可能にする。LangGraph固有APIの直接呼び出しは`graph.py`内に限定。


## 12. 戦闘力ロードマップ

| 時点 | 戦闘力 | マイルストーン |
|------|--------|-------------|
| **現在** | 15/100 | Execution 3ノード実装済み（executor + context_loader + formatter） |
| **M1: +sentinel +RAG** | 35/100 | 入力防御 + 知識検索 |
| **M1: +validator +strategist** | 50/100 | 出力品質保証 + 動的戦略 |
| **M1: +aggregator +並列 +Observability** | 60/100 | 並列実行 + 計測基盤。**Execution Layer完成** |
| **M2: +Lifecycle (L1)** | 70/100 | 設計の自動化（人間トリガー） |
| **M3: +Evolution** | 80/100 | 自律強化学習。**ここでカテゴリークリエイター** |
| **M4: +6社実戦検証** | 90/100 | 追いつけない壕ができる |
| **M6: +Lifecycle (L3)** | 95/100 | 完全自律設計。再帰的自己改善 |


---

> **最終更新**: 2026-02-22（v2 — ディープレビュー8件反映）
> **ディベート**: 全9ラウンド完走・戦略ロック済み
> **設計図完成度**: 90/100
> **次のアクション**: sentinel ノード実装（戦闘力 15 → 25）
