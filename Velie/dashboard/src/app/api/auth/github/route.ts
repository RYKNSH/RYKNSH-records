import { NextResponse, type NextRequest } from "next/server";

/**
 * POST /api/auth/github — Handle GitHub OAuth callback (mock for now).
 * In production, this would exchange the OAuth code for a Supabase session.
 */
export async function POST(request: NextRequest) {
    const { code } = await request.json();

    if (!code) {
        return NextResponse.json({ error: "Missing code parameter" }, { status: 400 });
    }

    // TODO: Exchange code with Supabase Auth
    // const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    // For now, set a demo session cookie
    const response = NextResponse.json({ success: true, redirect: "/dashboard" });
    response.cookies.set("velie_session", "demo_session", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: "/",
    });

    return response;
}
