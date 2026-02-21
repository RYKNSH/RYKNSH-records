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

### 3. The Boundary Protocol (境界管理の絶対ルール)
AIエージェントが親切心から他コンポーネントを修正し、システム全体を破壊（カスケーディング障害）することを防ぐためのデバッグ・スコープ管理ルール。

1. **Directory Isolation (ディレクトリ分離の原則)**
   現在担当している子会社のディレクトリ（例：`/Velie`）から一歩も外に出てはならない。他ディレクトリのコードは閲覧のみ許可され、修正は厳禁とする。
2. **The Shared Library Rule (共有基盤変更の禁止)**
   本社インフラ（`/Holdings`等）や共有DBスキーマの変更は、該当サブプロジェクトの開発中には絶対に行わない。必要な場合はFail Fastで停止する。
3. **Test-Boundary Enforcement (テスト境界の強制)**
   システム全体を動かしてデバッグしてはならない。必ず「対象コンポーネント単体のテスト（Unit Test）」を実行し、API境界を超えたエラーを発見した場合は、**相手のモックを作成して自領域のみ修正し、人間（CEO）へバグを報告する**。

---

## 🏢 Company Directory (子会社ディレクトリ)

RYKNSHホールディングスを構成する7つのAI子会社（LangGraphモジュール）と本社の正式名称マップです。
開発時は「QA Agent」や「広報AI」のような機能名ではなく、**この正式名称（Code Name）**を使用して明確に区別します。

| No | 正式名称 (Code Name) | 事業領域 (Role) | 外販プロダクト名 | 現在のステータス |
|:---|:---|:---|:---|:---|
| **0** | **RYKNSH records** | 本社・Orchestrator（全体指揮） | (なし) | `Planning` |
| **1** | **Velie** (ヴェリー) | 品質保証 (QA)・コード検証 | Velie CI | `Sprint 1 Core Done` |
| **2** | **Lumina** (ルミナ) | AI 制作プロダクション (画像/動画) | Lumina Studio | `Not Started` |
| **3** | **Cyrus** (サイラス) | グロース・マーケティング・自動営業 | Cyrus Growth | `Not Started` |
| **4** | **Iris** (アイリス) | 広報・炎上リスク管理・ブランド防衛 | Iris PR | `Not Started` |
| **5** | **Ada** (エイダ) | AI R&D・全エージェントの中枢基盤 | Ada Core API | `Not Started` |
| **6** | **Noah** (ノア) | ファンの熱狂を観測・集約する基盤 | Noah Platform | `Not Started` |
| **7** | **Label 01** (レーベル・ゼロワン) | 音楽レーベル・フラッグシップIP | (音楽コンテンツ) | `Not Started` |

### 📂 Repository & Module Routing
（実装開始後、各社がどのディレクトリ/リポジトリに配置されているかのパスをここに追記していきます。）

- **[0] RYKNSH records**: `/` (Mothership)
- **[1] Velie**: `/Velie/` (TBD)
- **[2] Lumina**: `/Lumina/` (TBD)
- **[3] Cyrus**: `/Cyrus/` (TBD)
- **[4] Iris**: `/Iris/` (TBD)
- **[5] Ada**: `/Ada/` (TBD)
- **[6] Noah**: `/Noah/` (TBD)
- **[7] Label 01**: `/Label01/` (TBD)

---
*Last Updated: 2026-02-21*
*Version: 1.2 (Project Navigator V12)*
