import { NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * GET /api/session — Return current session data from cookie.
 *
 * Response shape:
 * {
 *   authenticated: boolean;
 *   user: string;       // display name
 *   login: string;      // github login
 *   avatar: string;     // avatar URL
 *   plan: string;       // current plan key
 *   appId: string;      // GitHub App ID from env
 *   installationId: string; // GitHub App Installation ID from env
 * }
 */
export async function GET() {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("velie_session");

    if (!sessionCookie) {
        return NextResponse.json({
            authenticated: false,
            user: "",
            login: "",
            avatar: "",
            plan: "free",
            appId: process.env.GITHUB_APP_ID || "",
            installationId: process.env.GITHUB_APP_INSTALLATION_ID || "",
        });
    }

    try {
        const session = JSON.parse(sessionCookie.value);

        return NextResponse.json({
            authenticated: true,
            user: session.user || session.login || "",
            login: session.login || "",
            avatar: session.avatar || "",
            plan: session.plan || "free",
            appId: process.env.GITHUB_APP_ID || "",
            installationId: process.env.GITHUB_APP_INSTALLATION_ID || "",
        });
    } catch {
        return NextResponse.json({
            authenticated: false,
            user: "",
            login: "",
            avatar: "",
            plan: "free",
            appId: process.env.GITHUB_APP_ID || "",
            installationId: process.env.GITHUB_APP_INSTALLATION_ID || "",
        });
    }
}
