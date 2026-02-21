import { Sidebar } from "@/components/sidebar";
import { getReviews, timeAgo, type Review } from "@/lib/data";
import Link from "next/link";

export const revalidate = 10;

const severityConfig = {
    critical: { dot: "bg-red-500", label: "Critical", bg: "bg-red-500/10 text-red-400", icon: "🔴" },
    warning: { dot: "bg-amber-500", label: "Warning", bg: "bg-amber-500/10 text-amber-400", icon: "🟡" },
    clean: { dot: "bg-emerald-500", label: "Clean", bg: "bg-emerald-500/10 text-emerald-400", icon: "✅" },
};

function ReviewSection({ title, body }: { title: string; body: string }) {
    return (
        <div className="space-y-2">
            <h4 className="text-sm font-semibold text-purple-400">{title}</h4>
            <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {body}
            </div>
        </div>
    );
}

function parseReviewBody(body: string): { sections: { title: string; body: string }[] } {
    const sections: { title: string; body: string }[] = [];
    const lines = body.split("\n");
    let currentTitle = "";
    let currentBody: string[] = [];

    for (const line of lines) {
        if (line.startsWith("### ") || line.startsWith("## ")) {
            if (currentTitle || currentBody.length > 0) {
                sections.push({ title: currentTitle, body: currentBody.join("\n").trim() });
            }
            currentTitle = line.replace(/^#+\s*/, "");
            currentBody = [];
        } else {
            currentBody.push(line);
        }
    }
    if (currentTitle || currentBody.length > 0) {
        sections.push({ title: currentTitle, body: currentBody.join("\n").trim() });
    }
    return { sections };
}

export default async function ReviewDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const reviews = await getReviews(500);
    const review = reviews.find((r: Review) => r.id === decodeURIComponent(id));

    if (!review) {
        return (
            <div className="flex min-h-screen">
                <Sidebar />
                <main className="flex-1 ml-64 p-8">
                    <div className="glass p-12 text-center">
                        <span className="text-4xl block mb-4">🔍</span>
                        <p className="text-gray-400 text-lg">Review not found</p>
                        <Link href="/reviews" className="text-purple-400 text-sm mt-4 inline-block hover:text-purple-300">
                            ← Back to Reviews
                        </Link>
                    </div>
                </main>
            </div>
        );
    }

    const config = severityConfig[review.severity];
    const { sections } = parseReviewBody(review.review_body);

    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8 max-w-4xl">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
                    <Link href="/reviews" className="hover:text-purple-400 transition-colors">Reviews</Link>
                    <span>→</span>
                    <span className="text-gray-300">PR #{review.pr_number}</span>
                </div>

                {/* Header */}
                <div className="glass p-6 mb-6">
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                                <span className={`text-xs font-medium px-3 py-1 rounded-full ${config.bg}`}>
                                    {config.icon} {config.label}
                                </span>
                                <span className="text-xs text-gray-600">{timeAgo(review.created_at)}</span>
                            </div>
                            <h2 className="text-xl font-bold text-white mb-1">
                                {review.pr_title || `PR #${review.pr_number}`}
                            </h2>
                            <div className="flex items-center gap-3 text-sm text-gray-500">
                                <span>{review.repo_full_name}</span>
                                <span>·</span>
                                <span>by {review.pr_author}</span>
                                <span>·</span>
                                <span>PR #{review.pr_number}</span>
                            </div>
                        </div>
                        <a
                            href={`https://github.com/${review.repo_full_name}/pull/${review.pr_number}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs bg-white/5 hover:bg-white/10 text-gray-300 px-4 py-2 rounded-lg border border-white/10 transition-all"
                        >
                            View on GitHub ↗
                        </a>
                    </div>
                </div>

                {/* Review Body — Parsed Sections */}
                <div className="space-y-4">
                    {sections.map((section, i) => (
                        <div key={i} className="glass p-6">
                            <ReviewSection title={section.title} body={section.body} />
                        </div>
                    ))}
                </div>

                {/* Back link */}
                <div className="mt-8">
                    <Link href="/reviews" className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                        ← Back to all reviews
                    </Link>
                </div>
            </main>
        </div>
    );
}
