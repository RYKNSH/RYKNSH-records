---
description: RYKNSH records 本社（Mothership）開発セッション開始時の定型フロー。WHITEPAPER.mdを参照し指向性を確認してから開発に入る。
---

# /core-dev — RYKNSH records 本社開発ワークフロー

// turbo-all

## 1. 前回のコンテキスト復元

前回どこまで進んだかを最初に把握する：
- `~/.antigravity/NEXT_SESSION.md` があれば読み込む
- 直近のコミットを確認する：
  ```
  git log -n 5 --oneline
  ```

## 2. 全社の現在地を把握

- `docs/company_directory.md` を読み、全7子会社の最新ステータスを把握する

## 3. 判断の軸をロード

- `docs/strategy_bible.md` を読み、意思決定フレームワーク（理念→ビジョン→ミッション→戦略→戦術）を同期する

## 4. 今のPhaseと進行中のマイルストーン確認

- `docs/ROADMAP.md` を読み、現在のPhaseと本社の責務を確認する
- `docs/MILESTONES.md` を読み、進行中（🔶）のマイルストーンと完了条件を特定する

## 5. 今日のタスク選定

- `docs/TASKS.md` の「今すぐ着手可能なタスク」セクションから、優先度の高いタスクを選定してユーザーに提案する

提案時の優先順位ルール：
1. **依存関係の解消**: 他の多くのタスクがブロックされているタスクを最優先
2. **Phase順**: 現在のPhaseのタスクを優先
3. **本社タスク(HQ) > 統合タスク(INT)**: 本社固有のガバナンス系を優先

## 6. Boundary Protocol 確認

本社開発セッションでは以下の例外的権限を持つ：
- ✅ `/Holdings/` ディレクトリの変更
- ✅ `docs/` ディレクトリの全社ドキュメント更新
- ✅ 各子会社ディレクトリの README.md 更新

以下は **固く禁止**：
- ❌ 子会社のアプリケーションコード修正
- ❌ 子会社のDB migration / テストコード変更

## 7. 実行開始

ユーザーの承認を得たら `/go` で実行開始。

---

### 参照用ドキュメント（必要な時のみ）

| ファイル | いつ読む |
|---------|---------|
| `docs/WHITEPAPER.md` | 戦略の根拠を確認したい時 |
| `docs/architecture_blueprint.md` | システム設計に触る時 |
| `docs/master_execution_plan.md` | ROADMAP/MILESTONES に吸収済。参照のみ |
