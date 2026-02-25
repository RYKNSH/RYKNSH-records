---
description: 実装に入らず、ディープディベートラウンドだけでプロジェクトの詰めを行う純粋議論ワークフロー
---

# /refine - Deep Debate (No-Code Mode)

**Concept**: 実装は一切行わない「思考専用モード」。各ラウンドの議論をファイルとして記録し、思考プロセスそのものを資産として蓄積する。最終的なまとめは `/gen-dev` でホワイトペーパー化する。

> [!IMPORTANT]
> **実装禁止ルール（絶対遵守）**
> このワークフロー中は `/go`, `/new-feature`, `/build`, `/deploy` を呼び出してはいけない。
> コードブロックを書くことも禁止。出力は「思考・判断・議論」のみ。

> [!IMPORTANT]
> **品質基準（絶対遵守）**
> `/refine` は実装がない分、議論の品質は `/debate deep` を**超えなければならない**。
> 「議論に絞っているから深い」が正しい。絞っているのに浅いなら `/refine` を使う意味がない。

---

## 1. Trigger

```
/refine [テーマ]
/refine [テーマ] --rounds=N    # 最低ラウンド数を指定（default: 3）
/refine [テーマ] --until=consensus    # 全員合意まで無制限ループ
/refine [テーマ] --preset=titan       # 3巨頭チームで実行
```

---

## 2. ファイル管理（思考プロセスの記録）

> [!IMPORTANT]
> 各ラウンドが終わるたびに **即座にファイルを保存する**。会話で流れたら終わりではない。

### ファイル構造

```
[WHITEPAPER_DIR]/refine/[テーマスラッグ]/
  ├── _context.md          # Step 1: テーマ構造化 & チーム編成（初回のみ生成）
  ├── round_01.md          # Round 1 の全議論
  ├── round_02.md          # Round 2 の全議論
  ├── round_03.md          # Round 3 の全議論
  └── ...
```

**WHITEPAPER_DIR の決定ルール**:
1. プロジェクト固有の場合 → `[project_root]/docs/refine/`
2. グローバルな思考整理の場合 → `~/.antigravity/refine/`

**テーマスラッグ**: スペースをハイフンに変換、英数字 + ハイフンのみ。例: `new-project-concept`

### `_context.md` のフォーマット

```markdown
# Refine Session: [テーマ名]

**開始日時**: [ISO 8601]
**テーマスラッグ**: [slug]
**モード**: [rounds=N / until=consensus / default]

## 🎯 5軸分解

| 軸 | 内容 |
|---|---|
| Target | 誰のどんな課題を解決するか |
| Core Tension | 解決すべき根本的なトレードオフ |
| Risk | 主要リスク（技術/事業/ユーザー） |
| Unknowns | まだ分かっていない不確実性 |
| Success Criteria | 「詰まった」と判断できる基準 |

## 👥 Debate Team

| ペルソナ | 役割 | 種別 |
|---------|------|------|
| Skeptic | 全ての結論に「なぜ？」を繰り返す | 固定 |
| Devil's Advocate | 採用案の逆張りを提示し続ける | 固定 |
| [追加ペルソナ] | [役割] | テーマ連動 |

## 📁 Round Log

| Round | ファイル | 論点 | 判定 |
|-------|---------|------|------|
| (自動追記) |
```

### `round_N.md` のフォーマット

```markdown
# Round N: [このラウンドの論点]

**日時**: [ISO 8601]
**前ラウンドからの焦点**: [あれば記述]

---

## 議論

**🤔 Skeptic**:
[本質的な問い + Evidence（数値・事例・過去の決定）]

**😈 Devil's Advocate**:
[逆張り・別視点 + 前のペルソナへの反論/補強]

**[追加ペルソナ]**:
[専門領域からの批評 + 他ペルソナへの同意/反論/補強]

---

## 🧭 Moderator Summary

| 項目 | 内容 |
|------|------|
| 明確になったこと | |
| まだ詰まっていない論点 | |
| 次ラウンドの焦点 | |
| **判定** | `Continue` / `Deep Dive` / `New Angle` / `Conclude` |
```

---

## 3. ディベートループ（The Refine Loop）

```
Step 0: Knowledge Injection（必須・議論開始前に実行）
         ↓
Step 1: _context.md を生成（初回のみ）
         ↓
Step 2: チーム編成（_context.md の Team セクションに記録）
         ↓
Step 3: Round N を実行（以下のルールを厳格に守る）
         ↓
       round_N.md を即座に保存
         ↓
       _context.md の Round Log に1行追記
         ↓
       Moderator 判定
         ↓
     ┌── Continue / Deep Dive / New Angle → Step 3 (N+1) へ
     └── Conclude → Step 4 へ
          ↓
Step 4: Final Synthesis Report を生成
         ↓
Step 5: 完了通知（ファイル保存場所の一覧を表示）
```

### Step 0: Knowledge Injection（/debate 同等・必須）

議論を開始する前に、トピックに関連する知識を検索・注入する。

- `grep_search` でキーワード検索（`node_modules` 等の巨大ディレクトリは除外）
- 関連する `SKILL.md` やナレッジファイルを読み込む
- 既存のドキュメント（WHITEPAPER / DECISION_USECASES.md 等）を確認する

**この Step を飛ばした議論は「意見の垂れ流し」であり /refine の品質基準を満たさない。**

### Round N の品質ルール（/debate deep と同等以上）

- **Rule 1 (Criticism)**: 褒めるな。弱点・リスク・代替案を探せ。称賛は議論を止める。
- **Rule 2 (Evidence)**: 「なんとなく」は禁止。数値・事例・理論（検索したナレッジ・過去の決定）を根拠にせよ。
- **Rule 3 (Interaction)**: 他のペルソナの意見に必ず「同意」「反論」「補強」を行え。独立した意見を並べるだけでは /refine でない。
- **Rule 4 (Challenge)**: 最終ラウンドでも Moderator は「まだ詰めきれていない点がある」と仮定してアラ探しを続けよ。見かけ上の合意で早期終了するな。

### ループ継続条件

| 判定 | 条件 | アクション |
|------|------|-----------| 
| `Continue` | 重大な論点が残っている | 論点を絞って次ラウンドへ |
| `Deep Dive` | 表面的な議論に留まっている / Evidence が不十分 | 「なぜ？」をN回掘り下げて次ラウンドへ |
| `New Angle` | 議論が同じ場所を回っている | The Heretic を召喚し、前提ごとひっくり返す |
| `Conclude` | 全員の懸念が出尽くし、成功基準を満たした | Step 4 へ |

> [!NOTE]
> デフォルトで最低3ラウンド。見かけ上の合意が出ても Moderator は強制的に次ラウンドへ。
> 良い結論が出たように見えても「あえてアラ探し」を継続すること。

### Step 4: Final Synthesis Report（/debate deep 書式・必須）

```markdown
# 🏁 Final Debate Report
**テーマ**: [テーマ名]

## 💎 Refined Proposal (The Output)
[議論を経て磨き上げられた最終結論。簡潔に。]

## 🛡️ Addressed Concerns
- [解決済み] [懸念内容] → [解決策]（by [ペルソナ名]）

## ⚠️ Remaining Risks (Minor)
- [未解決] [リスク内容]（影響度: 高/中/低）

## 📊 Persona Contribution
| Persona | 最も鋭い貢献 | Impact |
|---------|------------|--------|
| ...     | ...        | High / Medium / Low |
```

---

## 4. Step 5: 完了通知

Final Report 生成後、保存済みファイルの一覧を出力する。

```markdown
✅ /refine セッション完了

## 📁 記録ファイル
- [_context.md](path)   ← テーマ構造 & チーム編成
- [round_01.md](path)   ← Round 1: [論点]
- [round_02.md](path)   ← Round 2: [論点]
- [round_N.md](path)    ← Round N: [論点]
- [final_report.md](path) ← Final Synthesis Report

## 🔜 次のアクション（ユーザーが判断）
- ホワイトペーパー化する場合 → `/gen-dev` でこのディレクトリを参照
- 仕様書にまとめる場合 → `/spec`
- 実装に進む場合 → `/go "[タスク名]"`
```

---

## 5. 実装トリガー禁止ガード

```
⛔ [REFINE MODE] 実装への遷移を検知しました。
このワークフローは議論専用です。
実装を開始する場合は明示的に /go を呼び出してください。
```

---

## 6. Cross-Reference

| 連携 | タイミング |
|------|-----------|
| `/gen-dev` | refine/ ディレクトリを参照してホワイトペーパー化 |
| `/spec` | refine 後、仕様書を形式化したい場合 |
| `/whitepaper` | refine 後、ビジョン・戦略文書にまとめる場合 |
| `/go` | ユーザーが明示的に実装開始を決断した場合のみ |
| `/debate` | AI主導の完全自律ディベート（実装まで進む可能性がある） |
