import { Sidebar } from "@/components/sidebar";
import { getDashboardStats } from "@/lib/data";

export const revalidate = 30;

const plans = [
    {
        name: "Free",
        price: "$0",
        period: "/mo",
        features: ["5 reviews/month", "1 repository", "Claude Haiku", "Community support"],
        current: true,
    },
    {
        name: "Pro",
        price: "$29",
        period: "/mo",
        features: ["Unlimited reviews", "10 repositories", "Claude Sonnet", "Priority support", "Custom prompts"],
        current: false,
        recommended: true,
    },
    {
        name: "Enterprise",
        price: "$99",
        period: "/mo",
        features: ["Unlimited everything", "Unlimited repos", "Claude Opus", "Dedicated support", "SSO / SAML", "Custom deployment"],
        current: false,
    },
];

const FREE_LIMIT = 5;

export default async function BillingPage() {
    const stats = await getDashboardStats();
    const usagePercent = Math.min((stats.totalReviews / FREE_LIMIT) * 100, 100);

    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white">Billing</h2>
                    <p className="text-sm text-gray-500 mt-1">Manage your subscription and usage</p>
                </div>

                {/* Current Usage — REAL DATA */}
                <div className="glass p-6 mb-8">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Current Usage</h3>
                    <div className="flex items-end gap-2 mb-3">
                        <span className="text-3xl font-bold text-white">{stats.totalReviews}</span>
                        <span className="text-gray-500 text-sm mb-1">/ {FREE_LIMIT} reviews</span>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all ${usagePercent >= 80 ? "bg-gradient-to-r from-red-500 to-red-400" : "bg-gradient-to-r from-purple-500 to-purple-400"
                                }`}
                            style={{ width: `${usagePercent}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                        {usagePercent >= 100 ? "⚠️ Limit reached — upgrade to Pro" : `${FREE_LIMIT - stats.totalReviews} reviews remaining`}
                    </p>
                </div>

                {/* Pricing Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {plans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`glass p-6 relative ${plan.recommended
                                    ? "border-purple-500/40 glow"
                                    : plan.current
                                        ? "border-emerald-500/30"
                                        : ""
                                }`}
                        >
                            {plan.recommended && (
                                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                                    Recommended
                                </span>
                            )}

                            <h4 className="text-lg font-bold text-white mb-1">{plan.name}</h4>
                            <div className="flex items-baseline gap-1 mb-4">
                                <span className="text-3xl font-bold text-white">{plan.price}</span>
                                <span className="text-sm text-gray-500">{plan.period}</span>
                            </div>

                            <ul className="space-y-2 mb-6">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-center gap-2 text-sm text-gray-400">
                                        <span className="text-emerald-400 text-xs">✓</span>
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            <button
                                className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all ${plan.current
                                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default"
                                        : plan.recommended
                                            ? "bg-purple-500 hover:bg-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/20"
                                            : "bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10"
                                    }`}
                                disabled={plan.current}
                            >
                                {plan.current ? "Current Plan" : "Upgrade"}
                            </button>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}
