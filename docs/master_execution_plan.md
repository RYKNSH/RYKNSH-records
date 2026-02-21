# RYKNSH records Master Execution Plan
> 何を、どの順番で作るか。最速で価値を生むための「Vertical Slice」ロードマップ

---

## 1. 開発順序の基本方針

### ❌ アンチパターン: 水平スライス (Horizontal Layers)
「まずSupabaseとRLSを完璧に設計し、次にLangGraphのオーケストレーター基盤を作り、最後に機能を乗せる」
→ **ユーザー（社内外の利用者）にとって、数カ月間「何も動かない」状態が続く。死を意味する。**

### ✅ RYNSHアプローチ: 垂直スライス (Vertical Slice)
「フロントエンドからDB、AIエージェントまでを貫通する『最も小さく、しかし完全に動くプロダクト』を最短でローンチし、それ単体で価値検証を行う」

---

## 2. 最初のターゲット：①品質保証AI (QA Agent)

RYKNSH recordsは「アーティスト以外全員AI」を目指す。
つまり、**AIが自分自身の書いたコードの品質を担保できなければ、他のAIエージェントをハイスピードで量産することは不可能**になる。

したがって、最初のVertical Sliceは **「自社のコード品質を担保し（内販）、同時に外部の開発チームにもSaaSとして販売できる（外販）」** ①品質保証AIの開発となる。Mothership（全体指揮AI）の開発は後回しとする。

---

## 3. QA Agent 実装スプリント (Phase 1)

このスプリントを消化することで、「単なるスクリプト」から「無限スケールするマルチテナントSaaS」へとシステムを進化させる。

### 🏃‍♂️ Sprint 1: The Core Loop (AIの脳と目の結合)
まずはインフラや記憶を無視し、「AIがコードを読んでレビューできる」最小ループを作る。

- ☑️ LangGraphで `qa_agent_graph` を定義（Claude/GPT-4o呼び出し）。
- ☑️ GitHub Webhookを受け取るFastAPI（またはNext.js Route）を構築。
- ☑️ PRが作成されるとWebhookが発火し、Agentが差分（Diff）を取得してPRにレビューコメントを投稿する。
- **マイルストーン**: 「とりあえずAIがPRを自動レビューしてくれるBot」の完成。

### 🧠 Sprint 2: The Multi-Tenant State (記憶と分離)
Sprint 1のBotに「文脈への記憶」と「マルチテナント分離」を持たせる。

- ☑️ Supabaseの構築と `tenant_id` カラムの追加。
- ☑️ Row Level Security (RLS) の設定。
- ☑️ LangGraph `AsyncPostgresSaver` をSupabaseに接続し、PRごとのスレッドIDで会話履歴を永続化（Stateful化）。
- ☑️ LangGraph `RunnableConfig` による、テナントごとのプロンプト（人格）動的注入。
- **マイルストーン**: 「過去の指摘を踏まえてレビューでき、他社のデータとは完全に隔離されたSaaSのバックエンド」の完成。

### 🚀 Sprint 3: The Scale Layer (無限スケールの担保)
ユーザーが増えても落ちないアーキテクチャへの進化。

- ☑️ Webhook受信層とLangGraph実行層を分離。
- ☑️ RedisまたはSQS等の Message Queue を導入。
- ☑️ リクエストはQueueに積まれ、背後の Serverless Worker 群が非同期でLangGraphを実行する構成に変更。
- **マイルストーン**: 「10万件のPRが同時に来ても決して落ちない、限界費用ゼロの無限スケール基盤」の完成。

### 🪟 Sprint 4: The Window (Studio Stream MVP)
バックエンドの状況を可視化し、顧客が設定等を行えるUIの構築。

- ☑️ Next.js + Vercel によるダッシュボード開発。
- ☑️ Supabaseと連携し、ユーザー（テナント管理者）が過去のレビュー履歴やAPI使用量を閲覧できるUI。
- ☑️ Stripeによるサブスクリプション/従量課金の連携。
- **マイルストーン**: 「有料で外部顧客に販売可能な完全なSaaSプロダクト (品質保証AI)」のローンチ。

---

## 4. Phase 1完了後の展開

Sprint 1〜4で構築した **[ GitHub -> Queue -> LangGraph -> Supabase -> UI ]** という垂直スライスのアーキテクチャは、RYKNSH recordsにおける「黄金の型」となる。

このアーキテクチャパターンをコピーし、LangGraphのAgent部分だけをすげ替えることで、以降の
- ② 制作会社 (Creative Graph)
- ④ 広報PR会社 (Press Graph)
などを、超高速で量産・デプロイしていくことが可能になる。

---
*Last Updated: 2026-02-21*
*Version: 1.0 (Master Execution Plan V9)*
