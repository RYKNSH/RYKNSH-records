import { NextResponse } from "next/server";

/**
 * POST /api/auth/logout — Clear session cookie.
 */
export async function POST() {
    const response = NextResponse.json({ success: true, redirect: "/" });
    response.cookies.delete("velie_session");
    return response;
}
