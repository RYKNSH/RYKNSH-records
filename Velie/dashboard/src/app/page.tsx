import Link from "next/link";

export const metadata = {
    title: "Velie — コードの安全は、Velieに任せて。",
    description: "GitHub AppをつなぐだけでAIが自動でコードレビュー。セキュリティ・バグ・品質の問題を検出し、ボタン1つで修正。バイブコーダーのための安全保障。",
};

const features = [
    { icon: "🛡️", title: "あなたのコード、大丈夫？", desc: "ハッキング、情報漏洩、バグ。AIが自動で見つけて、わかりやすく教えます。" },
    { icon: "🔧", title: "ボタン1つで修正", desc: "問題が見つかったら「修正する」を押すだけ。Velieが自動で直します。" },
    { icon: "🇯🇵", title: "日本語でわかりやすく", desc: "技術用語ではなく、誰でもわかる言葉で問題を説明します。" },
    { icon: "🧠", title: "使うほど賢くなる", desc: "あなたのリポジトリの過去のバグを学習し、同じ間違いを繰り返さないよう見守ります。" },
];

const steps = [
    { num: "1", title: "GitHubと繋ぐ", desc: "ボタン1つでインストール。30秒で完了。" },
    { num: "2", title: "コードを書く", desc: "いつも通り。Cursorでも、Copilotでも。" },
    { num: "3", title: "安心して公開", desc: "Velieが自動で見守り。安全スコアで一目瞭然。" },
];

const testimonials = [
    { quote: "コードは書けるけど、セキュリティが不安だった。Velieで安心して公開できるようになった。", name: "個人開発者 / デザイナー" },
    { quote: "SQLインジェクションって何？レベルだったけど、Velieが全部教えてくれる。", name: "起業家 / Cursor利用者" },
];

export default function LandingPage() {
    return (
        <div className="min-h-screen">
            {/* Background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/3 w-[600px] h-[600px] bg-purple-500/8 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-blue-500/8 rounded-full blur-3xl" />
                <div className="absolute top-1/2 right-1/3 w-[400px] h-[400px] bg-emerald-500/5 rounded-full blur-3xl" />
            </div>

            {/* Nav */}
            <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
                <h1 className="text-2xl font-bold">
                    <span className="glow-text text-purple-400">Velie</span>
                </h1>
                <div className="flex items-center gap-4">
                    <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                        ログイン
                    </Link>
                    <Link
                        href="/login"
                        className="text-sm bg-purple-500 hover:bg-purple-600 text-white px-5 py-2 rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/20"
                    >
                        無料で始める
                    </Link>
                </div>
            </nav>

            {/* Hero */}
            <section className="relative z-10 text-center px-8 pt-16 pb-20 max-w-4xl mx-auto">
                <div className="inline-block mb-6 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <span className="text-xs text-emerald-400 font-medium">🛡️ あなたのコードを24時間見守ります</span>
                </div>
                <h2 className="text-5xl md:text-6xl font-bold text-white leading-tight mb-6">
                    コードの安全は、<br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-emerald-400">
                        Velieに任せて。
                    </span>
                </h2>
                <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-10">
                    GitHubにつなぐだけ。AIがあなたのコードを自動でチェックして、
                    セキュリティの穴やバグを見つけたら、日本語でわかりやすく教えます。
                </p>
                <div className="flex items-center justify-center gap-4">
                    <Link
                        href="/login"
                        className="bg-purple-500 hover:bg-purple-600 text-white px-8 py-3.5 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/25"
                    >
                        今すぐ無料で始める →
                    </Link>
                    <Link
                        href="#how-it-works"
                        className="bg-white/5 hover:bg-white/10 text-gray-300 px-8 py-3.5 rounded-xl text-sm font-medium border border-white/10 transition-all"
                    >
                        仕組みを見る
                    </Link>
                </div>

                {/* Safety Score Preview */}
                <div className="mt-16 glass p-6 max-w-lg mx-auto text-left">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl">🛡️</span>
                        <span className="text-sm text-gray-400">あなたのリポジトリの安全スコア</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 rounded-xl bg-emerald-500/10">
                            <span className="text-3xl block mb-1">○</span>
                            <span className="text-xs text-emerald-400">安全</span>
                        </div>
                        <div className="text-center p-3 rounded-xl bg-amber-500/10">
                            <span className="text-3xl block mb-1">△</span>
                            <span className="text-xs text-amber-400">注意</span>
                        </div>
                        <div className="text-center p-3 rounded-xl bg-red-500/10">
                            <span className="text-3xl block mb-1">×</span>
                            <span className="text-xs text-red-400">危険</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="relative z-10 px-8 py-16 max-w-5xl mx-auto">
                <h3 className="text-2xl font-bold text-white text-center mb-4">Velieができること</h3>
                <p className="text-gray-500 text-center mb-12">エンジニアがいなくても、安心してコードを公開できます</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {features.map((f) => (
                        <div key={f.title} className="glass p-6 hover:border-purple-500/20 transition-all">
                            <span className="text-3xl mb-3 block">{f.icon}</span>
                            <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
                            <p className="text-sm text-gray-400">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* How it works */}
            <section id="how-it-works" className="relative z-10 px-8 py-16 max-w-4xl mx-auto">
                <h3 className="text-2xl font-bold text-white text-center mb-12">
                    3ステップで完了
                </h3>
                <div className="flex flex-col md:flex-row gap-8">
                    {steps.map((s) => (
                        <div key={s.num} className="flex-1 text-center">
                            <div className="w-14 h-14 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center mx-auto mb-4">
                                <span className="text-purple-400 font-bold text-lg">{s.num}</span>
                            </div>
                            <h4 className="text-white font-medium mb-2">{s.title}</h4>
                            <p className="text-sm text-gray-500">{s.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Demo: What Velie says */}
            <section className="relative z-10 px-8 py-16 max-w-3xl mx-auto">
                <h3 className="text-2xl font-bold text-white text-center mb-8">Velieはこう教えてくれます</h3>
                <div className="space-y-4">
                    <div className="glass p-5 border-l-4 border-red-500/60">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">×</span>
                            <span className="text-xs font-medium text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full">危険</span>
                        </div>
                        <p className="text-sm text-white font-medium mb-1">パスワードがコードに書いてあります</p>
                        <p className="text-xs text-gray-400 mb-3">ファイル: server/config.js — 15行目</p>
                        <p className="text-xs text-gray-500">パスワードをコードに直接書くと、GitHubに公開した瞬間に誰でも見えてしまいます。環境変数（.env）に移してください。</p>
                        <button className="mt-3 text-xs bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 px-4 py-2 rounded-lg transition-all">
                            🔧 ボタン1つで修正する
                        </button>
                    </div>
                    <div className="glass p-5 border-l-4 border-amber-500/60">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">△</span>
                            <span className="text-xs font-medium text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full">注意</span>
                        </div>
                        <p className="text-sm text-white font-medium mb-1">ユーザーの入力をそのまま使っています</p>
                        <p className="text-xs text-gray-400 mb-3">ファイル: api/users.js — 32行目</p>
                        <p className="text-xs text-gray-500">ユーザーが入力した文字をそのままデータベースの命令に使うと、攻撃者がデータを盗んだり消したりできます。</p>
                        <button className="mt-3 text-xs bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 px-4 py-2 rounded-lg transition-all">
                            🔧 ボタン1つで修正する
                        </button>
                    </div>
                </div>
            </section>

            {/* Social Proof */}
            <section className="relative z-10 px-8 py-16 max-w-4xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {testimonials.map((t) => (
                        <div key={t.name} className="glass p-6">
                            <p className="text-sm text-gray-300 mb-4 italic">&ldquo;{t.quote}&rdquo;</p>
                            <p className="text-xs text-gray-500">{t.name}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Pricing */}
            <section className="relative z-10 px-8 py-16 max-w-5xl mx-auto">
                <h3 className="text-2xl font-bold text-white text-center mb-4">料金プラン</h3>
                <p className="text-gray-500 text-center mb-12">まずは無料で。気に入ったらアップグレード。</p>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                    {[
                        { name: "無料", price: "¥0", period: "", features: ["1リポジトリ", "月5回レビュー", "安全スコア表示"], cta: "無料で始める", primary: false },
                        { name: "安心プラン", price: "¥980", period: "/月", features: ["3リポジトリ", "無制限レビュー", "日本語レビュー", "メール通知"], cta: "安心プランにする", primary: true },
                        { name: "プロ", price: "¥2,980", period: "/月", features: ["10リポジトリ", "ワンクリック修正", "優先サポート", "Slack連携"], cta: "プロにする", primary: false },
                        { name: "チーム", price: "¥9,800", period: "/月", features: ["無制限リポ", "SSO / SAML", "SLA保証", "専用サポート"], cta: "お問い合わせ", primary: false },
                    ].map((plan) => (
                        <div key={plan.name} className={`glass p-6 relative ${plan.primary ? "border-purple-500/40 glow" : ""}`}>
                            {plan.primary && (
                                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                                    人気
                                </span>
                            )}
                            <h4 className="text-lg font-bold text-white">{plan.name}</h4>
                            <div className="flex items-baseline gap-1 mb-4">
                                <span className="text-3xl font-bold text-white">{plan.price}</span>
                                {plan.period && <span className="text-sm text-gray-500">{plan.period}</span>}
                            </div>
                            <ul className="space-y-2 mb-6">
                                {plan.features.map((f) => (
                                    <li key={f} className="flex items-center gap-2 text-sm text-gray-400">
                                        <span className="text-emerald-400 text-xs">✓</span>{f}
                                    </li>
                                ))}
                            </ul>
                            <Link
                                href="/login"
                                className={`block text-center w-full py-2.5 rounded-xl text-sm font-medium transition-all ${plan.primary
                                    ? "bg-purple-500 hover:bg-purple-600 text-white"
                                    : "bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10"
                                    }`}
                            >
                                {plan.cta}
                            </Link>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section className="relative z-10 px-8 py-20 text-center">
                <h3 className="text-3xl font-bold text-white mb-4">コードの安全、今日から始めよう</h3>
                <p className="text-gray-400 mb-8">30秒でセットアップ完了。クレジットカード不要。</p>
                <Link
                    href="/login"
                    className="bg-purple-500 hover:bg-purple-600 text-white px-10 py-4 rounded-xl font-medium transition-all hover:shadow-lg hover:shadow-purple-500/25"
                >
                    今すぐ無料で始める →
                </Link>
            </section>

            {/* Footer */}
            <footer className="relative z-10 border-t border-white/5 px-8 py-8 text-center">
                <p className="text-xs text-gray-600">© 2026 RYKNSH records. All rights reserved.</p>
            </footer>
        </div>
    );
}
