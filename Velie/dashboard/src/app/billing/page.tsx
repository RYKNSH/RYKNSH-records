"use client";

import { Sidebar } from "@/components/sidebar";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useLocale } from "@/components/locale-context";

const planData = [
    {
        key: "free",
        nameKey: "plan.free" as const,
        price: { ja: "¥0", en: "$0", zh: "¥0" },
        featureKeys: ["feature.reviewsPerMonth", "feature.repos", "feature.communitySupport"] as const,
        featureParams: [{ n: 5 }, { n: 1 }, {}],
        model: "Claude Haiku",
        current: true,
    },
    {
        key: "anshin",
        nameKey: "plan.anshin" as const,
        price: { ja: "¥980", en: "$9", zh: "¥68" },
        featureKeys: ["feature.reviewsPerMonth", "feature.repos", "feature.emailSupport", "feature.japaneseReview"] as const,
        featureParams: [{ n: 50 }, { n: 5 }, {}, {}],
        model: "Claude Sonnet",
        current: false,
    },
    {
        key: "pro",
        nameKey: "plan.pro" as const,
        price: { ja: "¥2,980", en: "$29", zh: "¥198" },
        featureKeys: ["feature.unlimitedReviews", "feature.repos", "feature.prioritySupport", "feature.customPrompts", "feature.oneClickFix"] as const,
        featureParams: [{}, { n: 10 }, {}, {}, {}],
        model: "Claude Sonnet",
        current: false,
        recommended: true,
    },
    {
        key: "team",
        nameKey: "plan.team" as const,
        price: { ja: "¥9,800", en: "$99", zh: "¥688" },
        featureKeys: ["feature.unlimitedAll", "feature.unlimitedRepos", "feature.dedicatedSupport", "feature.ssoSaml", "feature.onPremise"] as const,
        featureParams: [{}, {}, {}, {}, {}],
        model: "Claude Opus",
        current: false,
    },
];

const FREE_LIMIT = 5;

interface DashboardStats {
    totalReviews: number;
    criticalIssues: number;
    repos: number;
    apiCalls: number;
}

function BillingContent() {
    const searchParams = useSearchParams();
    const { locale, t } = useLocale();
    const [stats, setStats] = useState<DashboardStats>({ totalReviews: 0, criticalIssues: 0, repos: 0, apiCalls: 0 });
    const [upgradeMessage, setUpgradeMessage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetch("/api/reviews")
            .then((r) => r.json())
            .then((reviews: { severity: string; repo_full_name: string }[]) => {
                const repos = new Set(reviews.map((r) => r.repo_full_name));
                setStats({
                    totalReviews: reviews.length,
                    criticalIssues: reviews.filter((r) => r.severity === "critical").length,
                    repos: repos.size,
                    apiCalls: reviews.length * 2,
                });
            })
            .catch(() => { });

        const success = searchParams.get("success");
        const canceled = searchParams.get("canceled");
        const plan = searchParams.get("plan");

        if (success) {
            setUpgradeMessage(`🎉 ${plan || "Pro"} ${t("billing.upgraded")}`);
        } else if (canceled) {
            setUpgradeMessage(t("billing.canceled"));
        } else if (searchParams.get("checkout") === "demo") {
            setUpgradeMessage(t("billing.demoMode"));
        }
    }, [searchParams, t]);

    const usagePercent = Math.min((stats.totalReviews / FREE_LIMIT) * 100, 100);

    async function handleUpgrade(planKey: string) {
        if (planKey === "free") return;
        setLoading(true);
        try {
            const res = await fetch("/api/billing/checkout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ plan: planKey }),
            });
            const data = await res.json();
            if (data.demo) {
                setUpgradeMessage(t("billing.demoMode"));
            } else if (data.url) {
                window.location.href = data.url;
            }
        } catch {
            setUpgradeMessage(t("billing.checkoutError"));
        }
        setLoading(false);
    }

    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white">{t("billing.title")}</h2>
                    <p className="text-sm text-gray-500 mt-1">{t("billing.subtitle")}</p>
                </div>

                {upgradeMessage && (
                    <div className="glass p-4 mb-6 border-purple-500/30">
                        <p className="text-sm text-purple-300">{upgradeMessage}</p>
                    </div>
                )}

                <div className="glass p-6 mb-8">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">{t("billing.currentUsage")}</h3>
                    <div className="flex items-end gap-2 mb-3">
                        <span className="text-3xl font-bold text-white">{stats.totalReviews}</span>
                        <span className="text-gray-500 text-sm mb-1">/ {FREE_LIMIT} {t("billing.reviews")}</span>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all ${usagePercent >= 80
                                ? "bg-gradient-to-r from-red-500 to-red-400"
                                : "bg-gradient-to-r from-purple-500 to-purple-400"
                                }`}
                            style={{ width: `${usagePercent}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                        {usagePercent >= 100
                            ? t("billing.limitReached")
                            : `${t("billing.remaining")} ${FREE_LIMIT - stats.totalReviews} ${t("billing.reviews")}`}
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {planData.map((plan) => (
                        <div
                            key={plan.key}
                            className={`glass p-6 relative ${plan.recommended
                                ? "border-purple-500/40 glow"
                                : plan.current
                                    ? "border-emerald-500/30"
                                    : ""
                                }`}
                        >
                            {plan.recommended && (
                                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-[10px] font-bold px-3 py-1 rounded-full tracking-wider">
                                    {t("billing.recommended")}
                                </span>
                            )}

                            <h4 className="text-lg font-bold text-white mb-1">{t(plan.nameKey)}</h4>
                            <div className="flex items-baseline gap-1 mb-1">
                                <span className="text-3xl font-bold text-white">{plan.price[locale]}</span>
                                <span className="text-sm text-gray-500">{t("billing.perMonth")}</span>
                            </div>
                            <p className="text-[10px] text-gray-600 mb-4">{plan.model}</p>

                            <ul className="space-y-2 mb-6">
                                {plan.featureKeys.map((fk, i) => (
                                    <li key={fk} className="flex items-center gap-2 text-sm text-gray-400">
                                        <span className="text-emerald-400 text-xs">✓</span>
                                        {t(fk, plan.featureParams[i] || undefined)}
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={() => handleUpgrade(plan.key)}
                                disabled={plan.current || loading}
                                className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer ${plan.current
                                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 !cursor-default"
                                    : plan.recommended
                                        ? "bg-purple-500 hover:bg-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/20"
                                        : "bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10"
                                    }`}
                            >
                                {plan.current ? t("billing.currentPlan") : loading ? t("billing.processing") : t("billing.upgrade")}
                            </button>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}

export default function BillingPage() {
    return (
        <Suspense fallback={<div className="flex min-h-screen"><Sidebar /><main className="flex-1 ml-64 p-8"><p className="text-gray-500">Loading...</p></main></div>}>
            <BillingContent />
        </Suspense>
    );
}
