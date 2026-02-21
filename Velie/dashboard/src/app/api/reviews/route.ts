import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

/**
 * GET /api/reviews — Read reviews from local JSON or Supabase.
 * This API route serves as the data bridge between backend and dashboard.
 */
export async function GET() {
    // Try local JSON first (backend writes here)
    const jsonPath = join(process.cwd(), "..", "data", "reviews.json");

    if (existsSync(jsonPath)) {
        try {
            const data = JSON.parse(readFileSync(jsonPath, "utf-8"));
            return NextResponse.json(data);
        } catch {
            return NextResponse.json([]);
        }
    }

    // Try Supabase
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (supabaseUrl && supabaseKey) {
        try {
            const res = await fetch(
                `${supabaseUrl}/rest/v1/reviews?order=created_at.desc&limit=100`,
                {
                    headers: {
                        apikey: supabaseKey,
                        Authorization: `Bearer ${supabaseKey}`,
                    },
                }
            );
            if (res.ok) {
                const data = await res.json();
                return NextResponse.json(data);
            }
        } catch {
            /* fall through */
        }
    }

    return NextResponse.json([]);
}
