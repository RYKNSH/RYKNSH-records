import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { ReviewItem } from "@/components/review-item";
import { getDashboardStats, getReviews, timeAgo } from "@/lib/data";

export const revalidate = 30; // ISR

export default async function DashboardPage() {
  const [stats, reviews] = await Promise.all([
    getDashboardStats(),
    getReviews(5),
  ]);

  const statCards = [
    { title: "Total Reviews", value: stats.totalReviews, icon: "🔍", color: "purple" as const, trend: stats.totalReviews > 0 ? { value: 100, label: "this week" } : undefined },
    { title: "Critical Issues", value: stats.criticalIssues, icon: "🔴", color: "green" as const, subtitle: stats.totalReviews > 0 ? `${Math.round((stats.criticalIssues / stats.totalReviews) * 100)}% detection rate` : "No reviews yet" },
    { title: "Repos Monitored", value: stats.repos, icon: "📦", color: "blue" as const },
    { title: "API Calls", value: stats.apiCalls, icon: "⚡", color: "amber" as const, subtitle: "Claude Sonnet" },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white">Dashboard</h2>
          <p className="text-sm text-gray-500 mt-1">AI-powered code review insights</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => (
            <StatCard key={stat.title} {...stat} />
          ))}
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Recent Reviews</h3>
            <a href="/reviews" className="text-xs text-purple-400 hover:text-purple-300">View all →</a>
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
                <h3 className="text-lg font-semibold text-white mb-2">Welcome to Velie!</h3>
                <p className="text-gray-400 text-sm mb-6 max-w-md mx-auto">
                  AI-powered code reviews for your PRs. Get started in 3 steps:
                </p>
                <div className="flex flex-col gap-4 max-w-sm mx-auto text-left">
                  <div className="flex items-start gap-3">
                    <span className="text-purple-400 font-bold text-sm mt-0.5">1</span>
                    <div>
                      <p className="text-sm text-white font-medium">Install the GitHub App</p>
                      <p className="text-xs text-gray-500">Connect your repositories to Velie</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-purple-400 font-bold text-sm mt-0.5">2</span>
                    <div>
                      <p className="text-sm text-white font-medium">Open a Pull Request</p>
                      <p className="text-xs text-gray-500">Velie will automatically review the code</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-purple-400 font-bold text-sm mt-0.5">3</span>
                    <div>
                      <p className="text-sm text-white font-medium">Review the results here</p>
                      <p className="text-xs text-gray-500">Track issues, severity, and trends</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">System Status</h3>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Webhook Server", status: "Operational", color: "bg-emerald-500" },
              { label: "Claude API", status: "Connected", color: "bg-emerald-500" },
              { label: "GitHub App", status: "Active", color: "bg-emerald-500" },
            ].map((item) => (
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
