import { Sidebar } from "@/components/sidebar";
import { ReviewItem } from "@/components/review-item";

// Mock data — will be replaced with Supabase queries
const allReviews = [
    {
        prNumber: 1,
        repo: "RYKNSH/RYKNSH-records",
        title: "test: Velie Real E2E - Security issue for review",
        author: "RYKNSH",
        severity: "critical" as const,
        createdAt: "2 hours ago",
    },
    {
        prNumber: 1,
        repo: "RYKNSH/RYKNSH-records",
        title: "test: Velie Real E2E - Security issue for review",
        author: "RYKNSH",
        severity: "warning" as const,
        createdAt: "3 hours ago",
    },
];

export default function ReviewsPage() {
    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-white">Reviews</h2>
                        <p className="text-sm text-gray-500 mt-1">All AI code review results</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {["All", "Critical", "Warning", "Clean"].map((filter) => (
                            <button
                                key={filter}
                                className={`px-4 py-2 rounded-xl text-xs font-medium transition-all ${filter === "All"
                                        ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                                        : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                                    }`}
                            >
                                {filter}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Reviews List */}
                <div className="space-y-3">
                    {allReviews.map((review, i) => (
                        <ReviewItem key={i} {...review} />
                    ))}
                </div>

                {/* Empty state hint */}
                {allReviews.length === 0 && (
                    <div className="glass p-12 text-center">
                        <span className="text-4xl mb-4 block">🔍</span>
                        <p className="text-gray-400">No reviews yet</p>
                        <p className="text-xs text-gray-600 mt-2">Open a PR in a monitored repo to trigger a review</p>
                    </div>
                )}
            </main>
        </div>
    );
}
