import { NextResponse, type NextRequest } from "next/server";

const GITHUB_CLIENT_ID = process.env.GITHUB_OAUTH_CLIENT_ID || "";
const GITHUB_CLIENT_SECRET = process.env.GITHUB_OAUTH_CLIENT_SECRET || "";

/**
 * GET /api/auth/github — Redirect to GitHub OAuth authorization page.
 */
export async function GET() {
    if (!GITHUB_CLIENT_ID) {
        // Demo mode - redirect to dashboard directly
        const response = NextResponse.redirect(new URL("/dashboard", process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"));
        response.cookies.set("velie_session", JSON.stringify({ user: "demo", login: "demo-user", avatar: "" }), {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "lax",
            maxAge: 60 * 60 * 24 * 7,
            path: "/",
        });
        return response;
    }

    const params = new URLSearchParams({
        client_id: GITHUB_CLIENT_ID,
        redirect_uri: `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/api/auth/github/callback`,
        scope: "read:user user:email",
        state: crypto.randomUUID(),
    });

    return NextResponse.redirect(`https://github.com/login/oauth/authorize?${params}`);
}

/**
 * POST /api/auth/github — Exchange OAuth code for session (legacy support).
 */
export async function POST(request: NextRequest) {
    const { code } = await request.json();

    if (!code) {
        return NextResponse.json({ error: "Missing code parameter" }, { status: 400 });
    }

    if (!GITHUB_CLIENT_ID || !GITHUB_CLIENT_SECRET) {
        // Demo mode
        const response = NextResponse.json({ success: true, redirect: "/dashboard" });
        response.cookies.set("velie_session", JSON.stringify({ user: "demo", login: "demo-user", avatar: "" }), {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "lax",
            maxAge: 60 * 60 * 24 * 7,
            path: "/",
        });
        return response;
    }

    // Exchange code for access token
    const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify({
            client_id: GITHUB_CLIENT_ID,
            client_secret: GITHUB_CLIENT_SECRET,
            code,
        }),
    });

    const tokenData = await tokenRes.json();
    if (tokenData.error) {
        return NextResponse.json({ error: tokenData.error_description }, { status: 400 });
    }

    // Get user info
    const userRes = await fetch("https://github.com/user", {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
    });
    const userData = await userRes.json();

    const session = {
        user: userData.name || userData.login,
        login: userData.login,
        avatar: userData.avatar_url,
        token: tokenData.access_token,
    };

    const response = NextResponse.json({ success: true, redirect: "/dashboard" });
    response.cookies.set("velie_session", JSON.stringify(session), {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7,
        path: "/",
    });

    return response;
}
