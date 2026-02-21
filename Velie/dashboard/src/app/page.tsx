import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { ReviewItem } from "@/components/review-item";

// Mock data — will be replaced with Supabase queries
const stats = [
  { title: "Total Reviews", value: 2, icon: "🔍", color: "purple" as const, trend: { value: 100, label: "this week" } },
  { title: "Critical Issues", value: 1, icon: "🔴", color: "green" as const, subtitle: "50% detection rate" },
  { title: "Repos Monitored", value: 1, icon: "📦", color: "blue" as const },
  { title: "API Calls", value: 4, icon: "⚡", color: "amber" as const, subtitle: "Claude Sonnet" },
];

const recentReviews = [
  {
    prNumber: 1,
    repo: "RYKNSH/RYKNSH-records",
    title: "test: Velie Real E2E - Security issue for review",
    author: "RYKNSH",
    severity: "critical" as const,
    createdAt: "2 hours ago",
  },
];

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white">Dashboard</h2>
          <p className="text-sm text-gray-500 mt-1">AI-powered code review insights</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat) => (
            <StatCard key={stat.title} {...stat} />
          ))}
        </div>

        {/* Recent Reviews */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Recent Reviews</h3>
            <span className="text-xs text-purple-400 cursor-pointer hover:text-purple-300">
              View all →
            </span>
          </div>
          <div className="space-y-3">
            {recentReviews.map((review) => (
              <ReviewItem key={`${review.repo}-${review.prNumber}`} {...review} />
            ))}
          </div>
        </div>

        {/* System Status */}
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
