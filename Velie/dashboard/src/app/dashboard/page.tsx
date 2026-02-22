import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { ReviewItem } from "@/components/review-item";
import { getDashboardStats, getReviews, timeAgo } from "@/lib/data";
import Link from "next/link";

export const revalidate = 30; // ISR

interface TrustData {
  trust_score: number;
  acceptance_rate: number;
  total_suggestions: number;
  trend: string;
}

interface HealthData {
  status: string;
  total_errors: number;
  recent_errors: number;
}

interface ReactionData {
  total: number;
  helpful: number;
  not_helpful: number;
  helpfulness_rate: number;
  nps_proxy: number;
}

async function getTrustScore(): Promise<TrustData> {
  try {
    const baseUrl = process.env.VELIE_API_URL || "http://localhost:8000";
    const res = await fetch(`${baseUrl}/api/trust`, { next: { revalidate: 60 } });
    if (!res.ok) return { trust_score: 0, acceptance_rate: 0, total_suggestions: 0, trend: "insufficient_data" };
    return await res.json();
  } catch {
    return { trust_score: 0, acceptance_rate: 0, total_suggestions: 0, trend: "insufficient_data" };
  }
}

async function getHealthStatus(): Promise<HealthData> {
  try {
    const baseUrl = process.env.VELIE_API_URL || "http://localhost:8000";
    const res = await fetch(`${baseUrl}/api/health/detailed`, { next: { revalidate: 30 } });
    if (!res.ok) return { status: "unknown", total_errors: 0, recent_errors: 0 };
    return await res.json();
  } catch {
    return { status: "unknown", total_errors: 0, recent_errors: 0 };
  }
}

async function getReactionStats(): Promise<ReactionData> {
  try {
    const baseUrl = process.env.VELIE_API_URL || "http://localhost:8000";
    const res = await fetch(`${baseUrl}/api/reactions/stats`, { next: { revalidate: 60 } });
    if (!res.ok) return { total: 0, helpful: 0, not_helpful: 0, helpfulness_rate: 0, nps_proxy: 0 };
    return await res.json();
  } catch {
    return { total: 0, helpful: 0, not_helpful: 0, helpfulness_rate: 0, nps_proxy: 0 };
  }
}

const healthStatusConfig: Record<string, { color: string; label: string }> = {
  healthy: { color: "bg-emerald-500", label: "正常" },
  warning: { color: "bg-amber-500", label: "注意" },
  degraded: { color: "bg-red-500", label: "異常" },
  unknown: { color: "bg-gray-500", label: "未接続" },
};

export default async function DashboardPage() {
  const [stats, reviews, trust, health, reactions] = await Promise.all([
    getDashboardStats(),
    getReviews(5),
    getTrustScore(),
    getHealthStatus(),
    getReactionStats(),
  ]);

  const trustPercent = Math.round(trust.trust_score * 100);
  const acceptancePercent = Math.round(trust.acceptance_rate * 100);
  const trendEmoji = trust.trend === "improving" ? "📈" : trust.trend === "declining" ? "📉" : "➡️";
  const helpfulPercent = Math.round(reactions.helpfulness_rate * 100);

  const statCards = [
    { title: "レビュー総数", value: stats.totalReviews, icon: "🔍", color: "purple" as const, trend: stats.totalReviews > 0 ? { value: 100, label: "今週" } : undefined },
    { title: "安全スコア", value: trustPercent, icon: "🛡️", color: "blue" as const, subtitle: trust.total_suggestions > 0 ? `承認率 ${acceptancePercent}% ${trendEmoji}` : "データなし" },
    { title: "満足度", value: `${helpfulPercent}%`, icon: "👍", color: "green" as const, subtitle: reactions.total > 0 ? `${reactions.total}件の評価 (NPS: ${reactions.nps_proxy > 0 ? "+" : ""}${reactions.nps_proxy})` : "評価なし" },
    { title: "危険検出", value: stats.criticalIssues, icon: "×", color: "amber" as const, subtitle: stats.totalReviews > 0 ? `検出率 ${Math.round((stats.criticalIssues / stats.totalReviews) * 100)}%` : "レビューなし" },
  ];

  const healthConfig = healthStatusConfig[health.status] || healthStatusConfig.unknown;

  const systemItems = [
    { label: "Webhookサーバー", status: healthConfig.label, color: healthConfig.color },
    { label: "Claude API", status: health.total_errors > 0 ? `最近のエラー: ${health.recent_errors}件` : "接続済み", color: health.recent_errors > 3 ? "bg-amber-500" : "bg-emerald-500" },
    { label: "GitHub App", status: "稼働中", color: "bg-emerald-500" },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white">ダッシュボード</h2>
          <p className="text-sm text-gray-500 mt-1">Velieのレビュー状況をひと目で確認</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => (
            <StatCard key={stat.title} {...stat} />
          ))}
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">最近のレビュー</h3>
            <a href="/reviews" className="text-xs text-purple-400 hover:text-purple-300">すべて見る →</a>
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
                  createdAt={timeAgo(review.created_at)}
                />
              ))
            ) : (
              <div className="glass p-10 text-center">
                <div className="text-5xl mb-4">🚀</div>
                <h3 className="text-lg font-semibold text-white mb-2">Velieへようこそ！</h3>
                <p className="text-gray-400 text-sm mb-6 max-w-md mx-auto">
                  AIがあなたのコードを守ります。3ステップで始めましょう：
                </p>
                <div className="flex flex-col gap-4 max-w-sm mx-auto text-left">
                  <div className="flex items-start gap-3">
                    <span className="text-purple-400 font-bold text-sm mt-0.5">1</span>
                    <div>
                      <p className="text-sm text-white font-medium">GitHubと繋ぐ</p>
                      <p className="text-xs text-gray-500">リポジトリをVelieに接続します</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-purple-400 font-bold text-sm mt-0.5">2</span>
                    <div>
                      <p className="text-sm text-white font-medium">Pull Requestを出す</p>
                      <p className="text-xs text-gray-500">Velieが自動でレビューします</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-purple-400 font-bold text-sm mt-0.5">3</span>
                    <div>
                      <p className="text-sm text-white font-medium">安全スコアを確認</p>
                      <p className="text-xs text-gray-500">○△×で結果がひと目でわかります</p>
                    </div>
                  </div>
                </div>
                <Link
                  href="/onboarding"
                  className="inline-block mt-6 bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded-xl text-sm font-medium transition-all"
                >
                  今すぐ始める →
                </Link>
              </div>
            )}
          </div>
        </div>

        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">システムステータス</h3>
          <div className="grid grid-cols-3 gap-4">
            {systemItems.map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <div className={`status-dot ${item.color}`} />
                <div>
                  <p className="text-sm text-gray-300">{item.label}</p>
                  <p className="text-xs text-gray-600">{item.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
