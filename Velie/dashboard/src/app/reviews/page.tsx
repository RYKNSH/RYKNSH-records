import { Sidebar } from "@/components/sidebar";
import { ReviewItem } from "@/components/review-item";
import { getReviews, timeAgo } from "@/lib/data";

export const revalidate = 30;

export default async function ReviewsPage() {
    const reviews = await getReviews(100);

    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-white">Reviews</h2>
                        <p className="text-sm text-gray-500 mt-1">
                            {reviews.length} review{reviews.length !== 1 ? "s" : ""} total
                        </p>
                    </div>
                </div>

                <div className="space-y-3">
                    {reviews.length > 0 ? (
                        reviews.map((review) => (
                            <ReviewItem
                                key={review.id}
                                prNumber={review.pr_number}
                                repo={review.repo_full_name}
                                title={review.pr_title || `PR #${review.pr_number}`}
                                author={review.pr_author}
                                severity={review.severity}
                                createdAt={timeAgo(review.created_at)}
                            />
                        ))
                    ) : (
                        <div className="glass p-12 text-center">
                            <span className="text-4xl mb-4 block">🔍</span>
                            <p className="text-gray-400">No reviews yet</p>
                            <p className="text-xs text-gray-600 mt-2">Open a PR in a monitored repo to trigger a review</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
