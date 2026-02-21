# RYKNSH records Company Directory
> The Map & The Meta-Loop (プロジェクト全体の羅針盤)

---

## 🔁 The Meta-Development Loop (開発迷子を防ぐ絶対ルール)

RYKNSH recordsは「人間1名と無数のAI」による超長期・大規模開発プロジェクトです。
各セッションでAIエージェントがコンテキストを見失い、無自覚にアーキテクチャや思想を破壊する（幻覚を元にコードを書く）ことを防ぐため、以下の**Meta-Loop（メタ・ループ）**を全セッションの開始時に必ず実行します。

### 1. State of the Union (セッション開始時の儀式)
いかなるタスク（実装・バグ修正・リファクタ）を開始する前にも、AIは以下の「4つのコンパス」を読み込み、現在の現在地と制約を同期しなければならない。

1. **`strategy_bible.md`**: なぜ作るのか。最終ビジョン（アーティスト以外全員AI）の確認。
2. **`architecture_blueprint.md`**: システムはどう繋がっているか（LangGraph/Supabase RLS/GitHub）の確認。
3. **`master_execution_plan.md`**: 次に何を作るべきか。現在のスプリントとその目標の確認。
4. **`company_directory.md` (本ドキュメント)**: どの会社（機能）の話をしているのか、全体マップの確認。

### 2. Git Driven Context Persistence (記憶のGit永続化)
AIエージェントの短期記憶を長期記憶に変換する。
- メインブランチ（`main`）には動くコードと確定したドキュメントのみをプッシュする。
- 開発コンテキスト（その日話し合った設計の機微や、なぜその技術を選んだかなど）は `ctx/log` のようなOrphanブランチ等を利用してスナップショットとして残す。

---

## 🏢 Company Directory (子会社ディレクトリ)

RYKNSHホールディングスを構成する7つのAI子会社（LangGraphモジュール）と本社の正式名称マップです。
開発時は「QA Agent」や「広報AI」のような機能名ではなく、**この正式名称（Code Name）**を使用して明確に区別します。

| No | 正式名称 (Code Name) | 事業領域 (Role) | 外販プロダクト名 | 現在のステータス |
|:---|:---|:---|:---|:---|
| **0** | **RYKNSH records** | 本社・Orchestrator（全体指揮） | (なし) | `Planning` |
| **1** | **Velie** (ヴェリー) | 品質保証 (QA)・コード検証 | Velie CI | `Sprint 1 準備中` |
| **2** | **Lumina** (ルミナ) | AI 制作プロダクション (画像/動画) | Lumina Creative Studio | `Not Started` |
| **3** | **Catalyst** (カタリスト) | グロース・マーケティング・自動営業 | Catalyst Growth Agent | `Not Started` |
| **4** | **Aegis** (イージス) | 広報・炎上リスク管理・ブランド防衛 | Aegis Crisis Shield | `Not Started` |
| **5** | **Core** (コア) | AI R&D・全エージェントのLLM/RAG基盤 | Core Agent Framework | `Not Started` |
| **6** | **Stream** (ストリーム) | ファン参加型コミュニティと課金基盤 | Studio Stream | `Not Started` |
| **7** | **Maison 01** (メゾン・ゼロワン) | 音楽レーベル・フラッグシップIP | (楽曲・音楽コンテンツ) | `Not Started` |

### 📂 Repository & Module Routing
（実装開始後、各社がどのディレクトリ/リポジトリに配置されているかのパスをここに追記していきます。）

- **[0] RYKNSH records**: `/` (Mothership)
- **[1] Velie**: `/Velie/` (TBD)
- **[2] Lumina**: `/Lumina/` (TBD)
- **[3] Catalyst**: `/Catalyst/` (TBD)
- **[4] Aegis**: `/Aegis/` (TBD)
- **[5] Core**: `/Core/` (TBD)
- **[6] Stream**: `/Stream/` (TBD)
- **[7] Maison 01**: `/Maison01/` (TBD)

---
*Last Updated: 2026-02-21*
*Version: 1.0 (Project Navigator V10)*
