---
description: Cyrus開発セッション開始時の定型フロー。WHITEPAPER.mdを参照し指向性を確認してから開発に入る。
---

# Cyrus開発セッション開始フロー

// turbo-all

## Step 1: 北極星を読む

1. `WHITEPAPER.md` を読み込む
```
cat /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus/WHITEPAPER.md
```

2. `ROADMAP.md` を読み込み、現在のマイルストーンとタスクを特定する
```
cat /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus/ROADMAP.md
```

## Step 2: 方向を確認する

3. 現在の戦闘力と次のアクションを確認する（WHITEPAPERのセクション12: 戦闘力ロードマップ）

4. 開発対象ノードが以下4-Layerのどこに位置するか明確にする:
   - 🔵 Intelligence Layer（市場分析・ICP・シグナル）
   - 🟢 Acquisition Layer（コンテンツ・アウトバウンド・バイラル・コミュニティ・呼び水）
   - 🟡 Conversion Layer（Trust Engine横断 + B2B/B2C/C2C 3パイプライン）
   - 🔴 Evolution Layer（パフォーマンス分析・A/B最適化）

5. Priority Weightsを確認:
   - 🏆 Outcome(0.40) > 📊 Quality(0.30) > ⚡ Speed(0.20) > 💰 Cost(0.10)

6. Boundary Protocolを確認（セクション10）:
   - Cyrus = マーケ戦略・営業フローの設計と実行
   - Lumina = クリエイティブ素材の制作（Cyrusは発注のみ）
   - Ada = LLM推論基盤の提供（Cyrusは呼び出しのみ）
   - Iris = ブランド保護・PR（Cyrusは集客、Irisは信頼）
   - Noah = マッチングPF（Cyrusは集客のみ）

## Step 3: 開発に入る

7. ROADMAPから今日のSprintのタスクを選び、implementation_planを策定する

8. 全ノードは `CyrusNode` 基底クラス（`engine/base.py`）を継承すること

9. コードベース構造:
   - `engine/` — グラフエンジン（state.py, base.py, graph.py）
   - `nodes/` — 全23ノード（intelligence/, acquisition/, conversion/, evolution/）
   - `models/` — データモデル（entity.py, blueprint.py, config.py）
   - `adapters/` — 外部データソースAdapter
   - `server/` — FastAPI（app.py, routes/）
   - `migrations/` — Supabase SQL
   - `tests/` — pytest

10. Entity差異は **Adapter Pattern** で処理:
   - Organization (B2B) / Individual (B2C) / Creator (C2C)
   - ノード内部でEntity Typeに応じたAdapterが動的選択

11. テスト実行:
```
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus && uv run pytest tests/ -v
```

12. サーバー起動:
```
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus && uv run python main.py
```

## 方向性を見失ったとき

WHITEPAPERの以下セクションに立ち返る:
- **セクション1**: Cyrusとは何か（自律グロースエンジン）
- **セクション3**: Entity Model v3（Organization/Individual/Creator）
- **セクション5**: Deep Personalization L3（Surface→Context→Empathy）
- **セクション6**: Trust Engine 5機能（Personality/Memory/Value-First/Timing/Score）
- **セクション7**: 全23ノード一覧
- **セクション9**: 価格モデル（Full Outcome 15-35%スライディング）
- **セクション10**: Boundary Protocol
- **セクション12**: 戦闘力ロードマップ

## 重要な設計原則

- **「操作」ではなく「適応」** — Trust Engineは相手を操作しない、相手に合わせる
- **Deep Personalization L3は「直接言及しない」** — 価値観に共鳴するトーンを「自然に」選ぶ
- **Full Outcome = 信頼の究極証明** — 「成功しなければ1円もいりません」
- **Always-On呼び水** — inbound_magnetは止まらない。市場が動くたびに新しい呼び水を自動生成
- **データ取得3階層** — L1:確実取得 → L2:許諾ベース → L3:推定→自動補正
