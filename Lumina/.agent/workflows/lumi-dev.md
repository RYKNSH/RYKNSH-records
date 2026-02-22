---
description: Lumina（AIクリエイティブプロダクション）開発セッション開始時の定型フロー。WHITEPAPER.mdを参照し指向性を確認してから開発に入る。
---

# /dev — Lumina Dev Session

**役割**: Luminaの開発セッションを開始するコマンド。
Whitepaper → Roadmap → マイルストーン → タスクの順でコンテキストを回復し、
正しい方向で実装に入る。

## Cross-Reference

```
/dev → whitepaper.md 参照 → 戦闘力ロードマップ参照 → /go "タスク"
/whitepaper で生成された Whitepaper-Driven Development の実行コマンド
```

---

## Phase 0: Context Recovery（コンテキスト回帰）

**目的**: プロジェクトの全体像を把握し、正しい方向で作業開始する。

// turbo-all

### 0-1. Whitepaper 熟読

```bash
cat /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Lumina/docs/whitepaper.md
```

以下を把握:
- **センターピン**: 納品物の絶対的クオリティが世界最高峰レベルを更新し続けること
- **5-Layer Architecture**: Intelligence / Creation / Quality Fortress / Delivery / Evolution
- **品質ティア**: Preview / Standard / Premium / Masterpiece
- **完全AIカンパニー**: ローンチ後の人間関与ゼロ（Autonomous Taste Calibration）
- **Boundary Protocol**: Luminaディレクトリ外のコードは絶対に触れない

### 0-2. ディベートデータ確認（必要時のみ）

```bash
head -20 /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Lumina/docs/lumina_quality_debate.md
```

設計判断の根拠が必要な場合にのみ参照。全8ラウンド（CEO承認済み）。

### 0-3. 戦闘力ロードマップ確認

Whitepaper Section 14を参照し、現在の戦闘力を特定:

| 時点 | 戦闘力 | マイルストーン |
|------|--------|-------------|
| **M2 W1: Creation MVP** | 10/100 | brief_interpreter + model_selector + generator |
| **M2 W2: +Quality Fortress** | 30/100 | taste_engine + quality_score_cascade |
| **M2 W3: +Enhancer + MV** | 50/100 | enhancer_pipeline + 映像生成。**Standard品質確立** |
| **M2 W4: +Delivery + PLG** | 60/100 | format_optimizer + asset_packager。Free Tier公開 |
| **M3: +Multi-Model + Premium** | 75/100 | multi_model_compositor。Premium品質確立 |
| **M3: +Evolution** | 85/100 | sota_watchdog + taste_calibrator + predictive_qc |
| **M4: +C2C Style Pack** | 90/100 | Noah連携。スタイルパックマーケットプレイス |
| **M6: +L3 Full Auto** | 95/100 | 完全自律 |

### 0-4. RYKNSH Boundary Protocol 確認

```bash
head -30 /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/docs/company_directory.md
```

> ⚠️ **絶対ルール**: コードは `/Lumina/` 内のみ。Ada/Velie/Cyrus/Iris/Noah/Label01のコードは触れない。共有基盤（Supabase schema等）の変更も禁止。

### 0-5. コンテキストサマリー出力

```markdown
📋 Lumina Context Recovery

**センターピン**: 納品物の絶対的クオリティが世界最高峰レベルを更新し続けること
**アーキテクチャ**: 5-Layer / 20ノード（完全AIカンパニー）
**現在のMS**: [戦闘力ロードマップから特定] — （戦闘力 X→Y）
**MS完了条件**: [対応するノード群の実装+テスト]
**残タスク**: [N]件
**前回の作業**: [最後のコミット or 状態]
```

---

## Phase 1: Task Selection（タスク選択）

**目的**: 次に取り組むべきタスクを特定し、ユーザーに提案する。

### 選択基準（優先順）

1. **前回の継続タスク**
2. **Whitepaperの戦闘力ロードマップ順**（依存関係に従う）
3. **工数「小」のタスク**を優先（モメンタム確保）
4. **ブロッカーがないタスク**

### ディレクトリ構造参照

```
src/graph/nodes/
├── intelligence/   ← 🔵 sota_watchdog, style_frontier_tracker, model_benchmarker
├── creation/       ← 🟢 brief_interpreter, model_selector, generator, enhancer_pipeline
├── quality/        ← 🟡 taste_engine, quality_score_cascade, ai_escalation_chain
├── delivery/       ← 🟠 format_optimizer, asset_packager, brand_consistency_check
└── evolution/      ← 🔴 performance_analyst, taste_calibrator, predictive_qc, sota_updater
```

### 提案フォーマット

```markdown
🎯 推奨タスク

1. **[ノード名]** — レイヤー: [🔵🟢🟡🟠🔴], 工数: [小/中/大]
   理由: [選択理由]

2. **[ノード名]** — レイヤー: [🔵🟢🟡🟠🔴], 工数: [小/中/大]
   理由: [選択理由]

どのタスクに取り組みますか？（番号 or 自由入力）
```

---

## Phase 2: Implementation（→ /go chain）

ユーザーが選択したタスクで実装開始:

```
/go "タスク名"
  → /work → /new-feature or /bug-fix or /refactor
  → /verify --quick
```

### 実装時の品質チェックリスト

- [ ] ノードは `src/graph/nodes/[layer]/` に配置しているか
- [ ] Pydanticモデルは `src/models/` に定義しているか
- [ ] テストは `tests/test_[area]/` に配置しているか
- [ ] Ada APIへの依存はモックで単体テスト可能か
- [ ] Boundary Protocol を遵守しているか（Luminaディレクトリ外を触っていないか）

---

## Phase 3: Milestone Check（MS品質ゲート）

タスク完了時にマイルストーン完了条件をチェック:

### 3-1. テスト実行

```bash
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Lumina
python -m pytest tests/ -v --tb=short
```

### 3-2. 型チェック

```bash
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Lumina
python -m mypy src/ --ignore-missing-imports
```

### 3-3. 戦闘力更新

マイルストーン完了時、Whitepaper の戦闘力ロードマップと照合:

```markdown
✅ [マイルストーン名] 完了 — [日時]
戦闘力: X → Y
テスト結果: [PASS/FAIL] ([件数])
```

### 3-4. 次のMSへ

未完了MSがあれば Phase 1 に戻る。
全MS完了 → `/ship` を提案。

---

## Quick Reference

| コマンド | 用途 |
|---------|------|
| `python -m pytest tests/ -v` | テスト実行 |
| `python -m mypy src/` | 型チェック |
| `cat docs/whitepaper.md` | Whitepaper参照 |
| `cat docs/lumina_quality_debate.md` | ディベート参照 |

## Dependencies（RYKNSH内）

```
Ada → Lumina: LLM推論リクエスト（API経由のみ）
Lumina → Cyrus/Iris/Noah/Label01: アセット納品
テスト時: Ada/Velie API依存はモックで代替
```
