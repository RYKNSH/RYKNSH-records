import Link from "next/link";

export const metadata = {
    title: "Velie — 使い方ガイド",
    description: "Velieの使い方を3ステップで簡単に説明します。",
};

const sections = [
    {
        title: "🔗 1. GitHubと繋ぐ",
        content: [
            "GitHubにログインした状態で「今すぐ無料で始める」ボタンを押します。",
            "Velie GitHub Appのインストール画面が表示されます。",
            "チェックしたいリポジトリを選んで「Install」を押します。",
            "これだけで接続完了です。30秒もかかりません。",
        ],
    },
    {
        title: "📝 2. コードを書いてPRを出す",
        content: [
            "いつも通りにコードを書きます。Cursor、Copilot、v0、何を使ってもOKです。",
            "GitHubでPull Requestを作成します。",
            "Velieが自動でコードをチェックし始めます。",
            "数分以内にレビュー結果がPRのコメントに届きます。",
        ],
    },
    {
        title: "🛡️ 3. 結果を確認する",
        content: [
            "ダッシュボードで安全スコアを確認できます。",
            "○（安全）：問題なし。安心してマージできます。",
            "△（注意）：軽微な問題があります。内容を確認してください。",
            "×（危険）：重大な問題があります。「🔧 修正する」ボタンで自動修正できます。",
        ],
    },
    {
        title: "🔧 ワンクリック修正",
        content: [
            "問題が見つかった場合、「修正する」ボタンを押すだけです。",
            "VelieのAIが自動で修正コードを生成し、Fix PRを作成します。",
            "あなたはFix PRをマージするだけ。コードを書く必要はありません。",
        ],
    },
    {
        title: "🇯🇵 日本語で説明",
        content: [
            "Velieは問題を日本語でわかりやすく説明します。",
            "技術用語は使いません。",
            "例：「SQLインジェクション」→「ユーザーの入力がそのままデータベースの命令として使われるため、攻撃者がデータを盗んだり消したりできます」",
        ],
    },
];

export default function DocsPage() {
    return (
        <div className="min-h-screen max-w-3xl mx-auto px-6 py-16">
            <div className="mb-12">
                <Link href="/" className="text-purple-400 hover:text-purple-300 text-sm transition-colors">
                    ← トップページに戻る
                </Link>
                <h1 className="text-3xl font-bold text-white mt-4 mb-2">使い方ガイド</h1>
                <p className="text-gray-500 text-sm">Velieを使い始めるために必要な全てがここにあります。</p>
            </div>

            <div className="space-y-8">
                {sections.map((section) => (
                    <div key={section.title} className="glass p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">{section.title}</h2>
                        <ol className="space-y-2">
                            {section.content.map((item, i) => (
                                <li key={i} className="flex gap-3 text-sm text-gray-400">
                                    <span className="text-purple-400/60 font-mono text-xs mt-0.5">{i + 1}.</span>
                                    {item}
                                </li>
                            ))}
                        </ol>
                    </div>
                ))}
            </div>

            <div className="mt-12 text-center">
                <Link
                    href="/onboarding"
                    className="bg-purple-500 hover:bg-purple-600 text-white px-8 py-3 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/20"
                >
                    今すぐ始める →
                </Link>
            </div>
        </div>
    );
}
