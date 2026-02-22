---
description: Cyrusの全テスト実行＋カバレッジ確認
---

# Cyrus テスト実行

// turbo-all

## Step 1: 全テスト実行

```
cd /Users/ryotarokonishi/Desktop/AntigravityWork/RYKNSH\ records/Cyrus && uv run pytest tests/ -v
```

## Step 2: 失敗時

1. エラーメッセージを読む
2. 該当ノードの `engine/base.py` → 対象ノードファイル → テストファイルの順に確認
3. mockデータと実装の整合性を確認（全ノードはAda API未設定時にmockフォールバック）

## Step 3: 新しいノード追加時

1. `nodes/{layer}/` にノードファイル作成（CyrusNode継承）
2. `engine/graph.py` にノード追加
3. `tests/test_{node_name}.py` 作成
4. テスト実行で確認
