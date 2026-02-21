import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware: protect dashboard routes.
 * Public routes: /, /login, /api/*
 * Protected routes: /dashboard, /reviews, /settings, /billing
 */

const PUBLIC_PATHS = ["/", "/login", "/api"];

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Allow public paths
    if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith("/api/"))) {
        return NextResponse.next();
    }

    // Allow static files
    if (pathname.startsWith("/_next") || pathname.includes(".")) {
        return NextResponse.next();
    }

    // Check for auth cookie (Supabase session or simple token)
    const authToken = request.cookies.get("velie_session")?.value;

    if (!authToken) {
        // Redirect to login
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("redirect", pathname);
        return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
