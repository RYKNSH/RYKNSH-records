# MS1: Creation MVP
> 戦闘力: 0 → 10/100
> 期間目安: M2 W1

---

## ゴール

**単一モデルで画像生成リクエストを受け付け、結果を返す最小パイプライン**を構築する。
LangGraphのグラフ定義、State管理、3つのCreation Layerノードの実装。

## 完了条件

- [ ] `brief_interpreter` ノードが自然言語ブリーフを構造化パラメータに変換できる
- [ ] `model_selector` ノードがModel Registryから最適モデルを選択できる
- [ ] `generator` ノードが選択されたモデルで画像を生成できる
- [ ] 3ノードがLangGraphで連結され、エンドツーエンドで動作する
- [ ] pytest で全ノードのユニットテスト + 統合テストが通る

## タスク分解

### 基盤（依存なし）

| ID | タスク | 工数 | 依存 | 状態 |
|----|--------|------|------|------|
| T1 | Lumina State（Pydantic）定義 | 小 | なし | ⬜ |
| T2 | CreativeBlueprint モデル定義 | 小 | なし | ⬜ |
| T3 | Model Registry テーブル設計 + クライアント | 中 | なし | ⬜ |

### ノード実装

| ID | タスク | 工数 | 依存 | 状態 |
|----|--------|------|------|------|
| T4 | `brief_interpreter` ノード実装 | 中 | T1, T2 | ⬜ |
| T5 | `model_selector` ノード実装 | 中 | T1, T3 | ⬜ |
| T6 | `generator` ノード実装 | 中 | T1, T3 | ⬜ |

### グラフ統合

| ID | タスク | 工数 | 依存 | 状態 |
|----|--------|------|------|------|
| T7 | LangGraph `lumina_graph.py` 定義 | 中 | T4, T5, T6 | ⬜ |
| T8 | FastAPI エンドポイント `/generate` | 小 | T7 | ⬜ |

### テスト

| ID | タスク | 工数 | 依存 | 状態 |
|----|--------|------|------|------|
| T9 | ユニットテスト（各ノード個別） | 中 | T4, T5, T6 | ⬜ |
| T10 | 統合テスト（グラフ全体E2E） | 中 | T7 | ⬜ |

## アーキテクチャメモ

```
[POST /generate]
  → brief_interpreter (ブリーフ解析)
  → model_selector (Model Registryから最適モデル選択)
  → generator (API呼び出し + 画像生成)
  → Response (生成物URL)
```

## 対象ディレクトリ

```
src/
├── models/
│   ├── state.py          ← T1: LuminaState
│   └── blueprint.py      ← T2: CreativeBlueprint
├── registry/
│   └── client.py         ← T3: ModelRegistryClient
├── graph/
│   ├── lumina_graph.py    ← T7: メインGraph
│   └── nodes/
│       └── creation/
│           ├── brief_interpreter.py  ← T4
│           ├── model_selector.py     ← T5
│           └── generator.py          ← T6
└── server/
    └── app.py             ← T8: FastAPI
tests/
├── test_graph/
│   ├── test_brief_interpreter.py  ← T9
│   ├── test_model_selector.py     ← T9
│   ├── test_generator.py          ← T9
│   └── test_lumina_graph.py       ← T10
└── test_registry/
    └── test_client.py             ← T9
```
