"use client";

import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { ReviewItem } from "@/components/review-item";
import { useLocale } from "@/components/locale-context";
import Link from "next/link";

interface SerializedReview {
    id: string;
    pr_number: number;
    repo_full_name: string;
    pr_title: string;
    pr_author: string;
    severity: "critical" | "warning" | "clean";
    created_at_relative: string;
}

interface Props {
    stats: { totalReviews: number; criticalIssues: number; repos: number; apiCalls: number };
    reviews: SerializedReview[];
    trust: { trust_score: number; acceptance_rate: number; total_suggestions: number; trend: string };
    health: { status: string; total_errors: number; recent_errors: number };
    reactions: { total: number; helpful: number; not_helpful: number; helpfulness_rate: number; nps_proxy: number };
}

const healthStatusKeys: Record<string, "health.healthy" | "health.warning" | "health.degraded" | "health.unknown"> = {
    healthy: "health.healthy",
    warning: "health.warning",
    degraded: "health.degraded",
    unknown: "health.unknown",
};

const healthColors: Record<string, string> = {
    healthy: "bg-emerald-500",
    warning: "bg-amber-500",
    degraded: "bg-red-500",
    unknown: "bg-gray-500",
};

export function DashboardContent({ stats, reviews, trust, health, reactions }: Props) {
    const { t } = useLocale();

    const trustPercent = Math.round(trust.trust_score * 100);
    const acceptancePercent = Math.round(trust.acceptance_rate * 100);
    const trendEmoji = trust.trend === "improving" ? "📈" : trust.trend === "declining" ? "📉" : "➡️";
    const helpfulPercent = Math.round(reactions.helpfulness_rate * 100);

    const statCards = [
        { title: t("dashboard.totalReviews"), value: stats.totalReviews, icon: "🔍", color: "purple" as const, trend: stats.totalReviews > 0 ? { value: 100, label: t("dashboard.thisWeek") } : undefined },
        { title: t("dashboard.safetyScore"), value: trustPercent, icon: "🛡️", color: "blue" as const, subtitle: trust.total_suggestions > 0 ? `${t("dashboard.acceptanceRate")} ${acceptancePercent}% ${trendEmoji}` : t("dashboard.noData") },
        { title: t("dashboard.satisfaction"), value: `${helpfulPercent}%`, icon: "👍", color: "green" as const, subtitle: reactions.total > 0 ? `${reactions.total} ${t("dashboard.ratings")} (NPS: ${reactions.nps_proxy > 0 ? "+" : ""}${reactions.nps_proxy})` : t("dashboard.noRating") },
        { title: t("dashboard.dangerDetection"), value: stats.criticalIssues, icon: "×", color: "amber" as const, subtitle: stats.totalReviews > 0 ? `${t("dashboard.detectionRate")} ${Math.round((stats.criticalIssues / stats.totalReviews) * 100)}%` : t("dashboard.noReview") },
    ];

    const healthKey = healthStatusKeys[health.status] || "health.unknown";
    const healthColor = healthColors[health.status] || healthColors.unknown;

    const systemItems = [
        { label: t("dashboard.webhookServer"), status: t(healthKey), color: healthColor },
        { label: "Claude API", status: health.total_errors > 0 ? `${t("dashboard.recentErrors")}: ${health.recent_errors}` : t("dashboard.connected"), color: health.recent_errors > 3 ? "bg-amber-500" : "bg-emerald-500" },
        { label: "GitHub App", status: t("dashboard.active"), color: "bg-emerald-500" },
    ];

    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white">{t("dashboard.title")}</h2>
                    <p className="text-sm text-gray-500 mt-1">{t("dashboard.subtitle")}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {statCards.map((stat) => (
                        <StatCard key={stat.title} {...stat} />
                    ))}
                </div>

                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white">{t("dashboard.recentReviews")}</h3>
                        <a href="/reviews" className="text-xs text-purple-400 hover:text-purple-300">{t("dashboard.viewAll")}</a>
                    </div>
                    <div className="space-y-3">
                        {reviews.length > 0 ? (
                            reviews.map((review) => (
                                <ReviewItem
                                    key={review.id}
                                    id={review.id}
                                    prNumber={review.pr_number}
                                    repo={review.repo_full_name}
                                    title={review.pr_title || `PR #${review.pr_number}`}
                                    author={review.pr_author}
                                    severity={review.severity}
                                    createdAt={review.created_at_relative}
                                />
                            ))
                        ) : (
                            <div className="glass p-10 text-center">
                                <div className="text-5xl mb-4">🚀</div>
                                <h3 className="text-lg font-semibold text-white mb-2">{t("dashboard.welcome")}</h3>
                                <p className="text-gray-400 text-sm mb-6 max-w-md mx-auto">
                                    {t("dashboard.welcomeDesc")}
                                </p>
                                <div className="flex flex-col gap-4 max-w-sm mx-auto text-left">
                                    <div className="flex items-start gap-3">
                                        <span className="text-purple-400 font-bold text-sm mt-0.5">1</span>
                                        <div>
                                            <p className="text-sm text-white font-medium">{t("dashboard.step1Title")}</p>
                                            <p className="text-xs text-gray-500">{t("dashboard.step1Desc")}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <span className="text-purple-400 font-bold text-sm mt-0.5">2</span>
                                        <div>
                                            <p className="text-sm text-white font-medium">{t("dashboard.step2Title")}</p>
                                            <p className="text-xs text-gray-500">{t("dashboard.step2Desc")}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <span className="text-purple-400 font-bold text-sm mt-0.5">3</span>
                                        <div>
                                            <p className="text-sm text-white font-medium">{t("dashboard.step3Title")}</p>
                                            <p className="text-xs text-gray-500">{t("dashboard.step3Desc")}</p>
                                        </div>
                                    </div>
                                </div>
                                <Link
                                    href="/onboarding"
                                    className="inline-block mt-6 bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded-xl text-sm font-medium transition-all"
                                >
                                    {t("dashboard.getStarted")}
                                </Link>
                            </div>
                        )}
                    </div>
                </div>

                <div className="glass p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">{t("dashboard.systemStatus")}</h3>
                    <div className="grid grid-cols-3 gap-4">
                        {systemItems.map((item) => (
                            <div key={item.label} className="flex items-center gap-3">
                                <div className={`status-dot ${item.color}`} />
                                <div>
                                    <p className="text-sm text-gray-300">{item.label}</p>
                                    <p className="text-xs text-gray-600">{item.status}</p>
                                    {item.color === "bg-gray-500" && (
                                        <Link href="/onboarding" className="text-[10px] text-purple-400 hover:text-purple-300 transition-colors">
                                            {t("dashboard.getStarted")} →
                                        </Link>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
}
