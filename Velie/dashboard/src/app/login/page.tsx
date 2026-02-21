import Link from "next/link";

export const metadata = {
    title: "Sign in to Velie CI",
    description: "AI-powered code review for your GitHub PRs",
};

export default function LoginPage() {
    const githubOAuthUrl = process.env.NEXT_PUBLIC_GITHUB_OAUTH_URL || "#";

    return (
        <div className="min-h-screen flex items-center justify-center">
            {/* Background gradient orbs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 w-full max-w-md px-6">
                {/* Logo */}
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-bold mb-2">
                        <span className="glow-text text-purple-400">Velie</span>
                        <span className="text-gray-500 text-lg ml-2 font-normal">CI</span>
                    </h1>
                    <p className="text-gray-500 text-sm">AI-powered code review for every PR</p>
                </div>

                {/* Login Card */}
                <div className="glass p-8">
                    <h2 className="text-xl font-semibold text-white text-center mb-2">Welcome back</h2>
                    <p className="text-sm text-gray-500 text-center mb-8">Sign in to your dashboard</p>

                    {/* GitHub OAuth Button */}
                    <a
                        href={githubOAuthUrl}
                        className="flex items-center justify-center gap-3 w-full py-3 rounded-xl bg-white text-gray-900 font-medium text-sm hover:bg-gray-100 transition-all hover:shadow-lg"
                    >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                        </svg>
                        Continue with GitHub
                    </a>

                    {/* Divider */}
                    <div className="flex items-center gap-4 my-6">
                        <div className="flex-1 h-px bg-white/10" />
                        <span className="text-xs text-gray-600">or</span>
                        <div className="flex-1 h-px bg-white/10" />
                    </div>

                    {/* Email (coming soon) */}
                    <div className="space-y-3">
                        <input
                            type="email"
                            placeholder="Email address"
                            disabled
                            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-500 placeholder-gray-600 cursor-not-allowed"
                        />
                        <button
                            disabled
                            className="w-full py-3 rounded-xl bg-purple-500/20 text-purple-400/50 font-medium text-sm cursor-not-allowed"
                        >
                            Coming soon
                        </button>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center mt-8 space-y-3">
                    <p className="text-xs text-gray-600">
                        By signing in, you agree to our{" "}
                        <span className="text-gray-500 hover:text-gray-400 cursor-pointer">Terms</span>{" "}
                        and{" "}
                        <span className="text-gray-500 hover:text-gray-400 cursor-pointer">Privacy Policy</span>
                    </p>
                    <Link href="/" className="text-xs text-purple-400 hover:text-purple-300 block">
                        ← Back to home
                    </Link>
                </div>
            </div>
        </div>
    );
}
