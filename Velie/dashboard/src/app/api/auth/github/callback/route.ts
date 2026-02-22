import { NextResponse, type NextRequest } from "next/server";

const GITHUB_CLIENT_ID = process.env.GITHUB_OAUTH_CLIENT_ID || "";
const GITHUB_CLIENT_SECRET = process.env.GITHUB_OAUTH_CLIENT_SECRET || "";

/**
 * GET /api/auth/github/callback — Handle GitHub OAuth callback.
 */
export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");

    if (!code) {
        return NextResponse.redirect(new URL("/login?error=no_code", request.url));
    }

    try {
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
            return NextResponse.redirect(new URL(`/login?error=${tokenData.error}`, request.url));
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

        const response = NextResponse.redirect(new URL("/dashboard", request.url));
        response.cookies.set("velie_session", JSON.stringify(session), {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "lax",
            maxAge: 60 * 60 * 24 * 7,
            path: "/",
        });

        return response;
    } catch {
        return NextResponse.redirect(new URL("/login?error=oauth_failed", request.url));
    }
}
