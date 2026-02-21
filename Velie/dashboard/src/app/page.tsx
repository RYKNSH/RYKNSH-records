import Link from "next/link";

export const metadata = {
    title: "Velie CI — AI Code Review for Every PR",
    description: "Automated, intelligent code reviews powered by Claude. Catch bugs, security issues, and code quality problems before they ship.",
};

const features = [
    { icon: "🔍", title: "Deep Code Analysis", desc: "Claude AI reviews every PR for security, performance, and code quality" },
    { icon: "⚡", title: "Instant Feedback", desc: "Reviews posted as PR comments within seconds of opening" },
    { icon: "🔒", title: "Security First", desc: "Detect hardcoded secrets, SQL injection, XSS, and more" },
    { icon: "📊", title: "Dashboard Insights", desc: "Track review trends, severity, and team health" },
];

const steps = [
    { num: "1", title: "Install the GitHub App", desc: "One-click install. Select your repositories." },
    { num: "2", title: "Open a Pull Request", desc: "Velie automatically reviews every PR." },
    { num: "3", title: "Ship with confidence", desc: "Catch issues before they hit production." },
];

export default function LandingPage() {
    return (
        <div className="min-h-screen">
            {/* Background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/3 w-[600px] h-[600px] bg-purple-500/8 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-blue-500/8 rounded-full blur-3xl" />
            </div>

            {/* Nav */}
            <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
                <h1 className="text-2xl font-bold">
                    <span className="glow-text text-purple-400">Velie</span>
                    <span className="text-gray-500 text-sm ml-2 font-normal">CI</span>
                </h1>
                <div className="flex items-center gap-4">
                    <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                        Sign in
                    </Link>
                    <Link
                        href="/login"
                        className="text-sm bg-purple-500 hover:bg-purple-600 text-white px-5 py-2 rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/20"
                    >
                        Get started free
                    </Link>
                </div>
            </nav>

            {/* Hero */}
            <section className="relative z-10 text-center px-8 pt-16 pb-20 max-w-4xl mx-auto">
                <div className="inline-block mb-6 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20">
                    <span className="text-xs text-purple-400 font-medium">Powered by Claude Sonnet</span>
                </div>
                <h2 className="text-5xl md:text-6xl font-bold text-white leading-tight mb-6">
                    AI code reviews that<br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                        actually catch bugs
                    </span>
                </h2>
                <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-10">
                    Every pull request reviewed by Claude in seconds.
                    Security vulnerabilities, code quality issues, and best practices — automatically.
                </p>
                <div className="flex items-center justify-center gap-4">
                    <Link
                        href="/login"
                        className="bg-purple-500 hover:bg-purple-600 text-white px-8 py-3.5 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/25"
                    >
                        Start reviewing for free →
                    </Link>
                    <a
                        href="https://github.com/apps/velie-qa-agent"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-white/5 hover:bg-white/10 text-gray-300 px-8 py-3.5 rounded-xl text-sm font-medium border border-white/10 transition-all"
                    >
                        View on GitHub
                    </a>
                </div>
            </section>

            {/* Features */}
            <section className="relative z-10 px-8 py-16 max-w-5xl mx-auto">
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
            <section className="relative z-10 px-8 py-16 max-w-4xl mx-auto">
                <h3 className="text-2xl font-bold text-white text-center mb-12">
                    How it works
                </h3>
                <div className="flex flex-col md:flex-row gap-8">
                    {steps.map((s) => (
                        <div key={s.num} className="flex-1 text-center">
                            <div className="w-12 h-12 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center mx-auto mb-4">
                                <span className="text-purple-400 font-bold">{s.num}</span>
                            </div>
                            <h4 className="text-white font-medium mb-2">{s.title}</h4>
                            <p className="text-sm text-gray-500">{s.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Pricing */}
            <section className="relative z-10 px-8 py-16 max-w-5xl mx-auto">
                <h3 className="text-2xl font-bold text-white text-center mb-4">Simple pricing</h3>
                <p className="text-gray-500 text-center mb-12">Start free, upgrade when you need more</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        { name: "Free", price: "$0", features: ["5 reviews/month", "1 repo", "Claude Haiku"], cta: "Get started", primary: false },
                        { name: "Pro", price: "$29", features: ["Unlimited reviews", "10 repos", "Claude Sonnet", "Priority support"], cta: "Start free trial", primary: true },
                        { name: "Enterprise", price: "$99", features: ["Unlimited everything", "Claude Opus", "SSO/SAML", "Custom deployment"], cta: "Contact sales", primary: false },
                    ].map((plan) => (
                        <div key={plan.name} className={`glass p-6 relative ${plan.primary ? "border-purple-500/40 glow" : ""}`}>
                            {plan.primary && (
                                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                                    Popular
                                </span>
                            )}
                            <h4 className="text-lg font-bold text-white">{plan.name}</h4>
                            <div className="flex items-baseline gap-1 mb-4">
                                <span className="text-3xl font-bold text-white">{plan.price}</span>
                                <span className="text-sm text-gray-500">/mo</span>
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
                <h3 className="text-3xl font-bold text-white mb-4">Ready to ship better code?</h3>
                <p className="text-gray-400 mb-8">Join developers who trust Velie for every PR.</p>
                <Link
                    href="/login"
                    className="bg-purple-500 hover:bg-purple-600 text-white px-10 py-4 rounded-xl font-medium transition-all hover:shadow-lg hover:shadow-purple-500/25"
                >
                    Get started free →
                </Link>
            </section>

            {/* Footer */}
            <footer className="relative z-10 border-t border-white/5 px-8 py-8 text-center">
                <p className="text-xs text-gray-600">© 2026 RYKNSH records. All rights reserved.</p>
            </footer>
        </div>
    );
}
