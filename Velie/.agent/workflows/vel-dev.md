---
description: Velie開発専用 - ホワイトペーパー→ロードマップ→マイルストーン読み込み後に/goで実装開始
---

# /vel-dev - Velie Development Mode

**役割**: Velieプロジェクト専用の開発ワークフロー。戦略文書を読み込んだ上で実装に入る。

// turbo-all

## 手順

### 1. ホワイトペーパー読み込み
Velieのビジョン・ミッション・プロダクト原則を確認する。

```
view_file: /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH records/Velie/docs/WHITEPAPER.md
```

### 2. ロードマップ読み込み
M1〜M4のマイルストーンと全タスクを確認する。

```
view_file: /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH records/Velie/docs/ROADMAP.md
```

### 3. 現在のタスク進捗確認
task.mdの現在のチェックリスト状態を確認する。

```
view_file: <appDataDir>/brain/<conversation-id>/task.md
```

### 4. 次のタスク特定
ロードマップとtask.mdから、**次に着手すべき未完了タスク**を特定する。

判定ロジック:
- task.mdで `[ ]` のタスクを上から順にスキャン
- ロードマップのマイルストーン順（M1→M2→M3→M4）に従う
- 各マイルストーン内はサブタスク番号順（M1-1→M1-2→...）

### 5. プロダクト原則チェック
実装に入る前に、ホワイトペーパーの5原則を再確認:
1. 3ステップで完了
2. 日本語で話す
3. 安心を売る
4. ボタン1つで直る
5. 静かに守る

> [!IMPORTANT]
> 全ての実装判断はこの5原則に照らして行う。原則に反する実装はやらない。

### 6. /go 実行
特定したタスクに対して実装を開始する。

- task.mdの該当タスクを `[/]` に更新
- 実装 → テスト → コミット → task.mdを `[x]` に更新
- 完了したら次のタスクに自動で移行
- 全マイルストーンのタスクが完了するまで繰り返す

### 7. 完了チェック
各マイルストーン完了時:
- `uv run pytest tests/ -v` 全テスト合格確認
- `cd dashboard && npx next build` ビルド成功確認
- gitコミット＆プッシュ
- 次のマイルストーンへ
