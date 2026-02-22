---
description: Ada開発セッション開始時の定型フロー。WHITEPAPER.mdを参照し指向性を確認してから開発に入る。
---

# Ada開発セッション開始フロー

// turbo-all

## Step 1: 北極星を読む

1. `WHITEPAPER.md` を読み込む
```
cat WHITEPAPER.md
```

2. `ROADMAP.md` を読み込み、現在のマイルストーンとタスクを特定する
```
cat ROADMAP.md
```

## Step 2: 方向を確認する

3. 現在の戦闘力と次のアクションを確認する（WHITEPAPERのセクション12: 戦闘力ロードマップ）

4. 開発対象ノードが以下3-Layerのどこに位置するか明確にする:
   - 🔵 LIFECYCLE（設計時1回）
   - 🟢 EXECUTION（毎リクエスト）
   - 🔴 EVOLUTION（定期バッチ）
   - 🛡️ SECURITY（横断的）

5. Priority Weightsを確認（セクション4）:
   - 🏆 品質(0.40) > ⚡ 効率(0.30) > 🚀 速度(0.20) > 🪶 軽量(0.10)

6. Boundary Protocolを確認（セクション9）:
   - Ada = ノードパターン（型）を提供
   - 子会社 = ツールとプロンプト（素材）を提供
   - 業務ロジックに踏み込まない

## Step 3: 開発に入る

7. ROADMAPから今日のMSのタスクを選び、implementation_planを策定する

8. 全ノードは `AdaNode` 基底クラス（`agent/nodes/base.py`）を継承すること

9. コードベース構造:
   - `agent/` — コアロジック（nodes/, tools/, rag/, lifecycle/, evolution/）
   - `server/` — FastAPI（app.py, config.py, rate_limit.py）
   - `tests/` — pytest

10. テスト実行:
```
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Ada && python -m pytest tests/ -v
```

## 方向性を見失ったとき

WHITEPAPERの以下セクションに立ち返る:
- **セクション1**: Adaとは何か（鎧制師が自分の鎧を自分で作る）
- **セクション2**: 3-Layer Architecture
- **セクション4**: Priority Weights
- **セクション6**: AgentBlueprint（Lifecycle → Execution接続）
- **セクション9**: Boundary Protocol
