/**
 * Velie CI Dashboard — Data Layer.
 *
 * Fetches from:
 * 1. /api/reviews (local dev — reads data/reviews.json)
 * 2. Supabase REST API (production fallback)
 */

export interface Review {
    id: string;
    pr_number: number;
    repo_full_name: string;
    pr_title: string;
    pr_author: string;
    severity: "critical" | "warning" | "clean";
    review_body: string;
    installation_id: number | null;
    created_at: string;
}

function getBaseUrl(): string {
    // Server-side: use internal URL
    if (typeof window === "undefined") {
        return process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
    }
    return "";
}

export async function getReviews(limit = 50): Promise<Review[]> {
    try {
        const res = await fetch(`${getBaseUrl()}/api/reviews`, {
            next: { revalidate: 10 },
        });
        if (!res.ok) return [];
        const data: Review[] = await res.json();
        return data.slice(0, limit);
    } catch {
        return [];
    }
}

export interface DashboardStats {
    totalReviews: number;
    criticalIssues: number;
    repos: number;
    apiCalls: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
    const reviews = await getReviews(1000);

    const repos = new Set(reviews.map((r) => r.repo_full_name));
    const criticalCount = reviews.filter((r) => r.severity === "critical").length;

    return {
        totalReviews: reviews.length,
        criticalIssues: criticalCount,
        repos: repos.size,
        apiCalls: reviews.length * 2,
    };
}

export function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}
