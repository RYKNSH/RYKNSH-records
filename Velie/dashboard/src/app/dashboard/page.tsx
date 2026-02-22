import { getDashboardStats, getReviews, timeAgo, type Review } from "@/lib/data";
import { DashboardContent } from "@/components/dashboard-content";

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

export default async function DashboardPage() {
  const [stats, reviews, trust, health, reactions] = await Promise.all([
    getDashboardStats(),
    getReviews(5),
    getTrustScore(),
    getHealthStatus(),
    getReactionStats(),
  ]);

  // Serialize reviews for client component
  const serializedReviews = reviews.map((r: Review) => ({
    id: r.id,
    pr_number: r.pr_number,
    repo_full_name: r.repo_full_name,
    pr_title: r.pr_title,
    pr_author: r.pr_author,
    severity: r.severity,
    created_at_relative: timeAgo(r.created_at),
  }));

  return (
    <DashboardContent
      stats={stats}
      reviews={serializedReviews}
      trust={trust}
      health={health}
      reactions={reactions}
    />
  );
}
