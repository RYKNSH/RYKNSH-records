import { NextResponse } from "next/server";

export async function POST(request: Request) {
    const body = await request.json();
    const { reviewId, repo, prNumber } = body;

    if (!reviewId || !repo || !prNumber) {
        return NextResponse.json(
            { error: "Missing required fields: reviewId, repo, prNumber" },
            { status: 400 },
        );
    }

    try {
        // Call the Velie backend autofix endpoint
        const baseUrl = process.env.VELIE_API_URL || "http://localhost:8000";
        const res = await fetch(`${baseUrl}/api/autofix`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ review_id: reviewId, repo, pr_number: prNumber }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            return NextResponse.json(
                { error: data.detail || "Failed to create fix PR", status: "error" },
                { status: res.status },
            );
        }

        const data = await res.json();
        return NextResponse.json({
            success: true,
            fix_pr_url: data.fix_pr_url || null,
            message: data.message || "修正PRを作成しました",
        });
    } catch {
        return NextResponse.json(
            { error: "Velie server is not reachable", status: "error" },
            { status: 503 },
        );
    }
}
