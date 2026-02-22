import { NextResponse } from "next/server";

// Velie pricing plan → Stripe Price ID mapping
const PRICE_IDS: Record<string, string> = {
    free: "",
    anshin: process.env.STRIPE_PRICE_ANSHIN || "",      // ¥980/月
    pro: process.env.STRIPE_PRICE_PRO || "",             // ¥2,980/月
    team: process.env.STRIPE_PRICE_TEAM || "",           // ¥9,800/月
};

/**
 * POST /api/billing/checkout — Create Stripe Checkout session.
 */
export async function POST(request: Request) {
    const { plan } = await request.json();

    if (!plan || plan === "free") {
        return NextResponse.json({ url: "/dashboard", demo: false });
    }

    const stripeKey = process.env.STRIPE_SECRET_KEY;

    if (!stripeKey) {
        // Demo mode
        return NextResponse.json({
            url: `/billing?plan=${plan}&checkout=demo`,
            demo: true,
        });
    }

    try {
        // Dynamic import to avoid build errors when Stripe not installed
        const Stripe = (await import("stripe")).default;
        const stripe = new Stripe(stripeKey);

        const priceId = PRICE_IDS[plan];
        if (!priceId) {
            return NextResponse.json({ error: "Invalid plan" }, { status: 400 });
        }

        const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

        const session = await stripe.checkout.sessions.create({
            mode: "subscription",
            line_items: [{ price: priceId, quantity: 1 }],
            success_url: `${siteUrl}/billing?success=true&plan=${plan}`,
            cancel_url: `${siteUrl}/billing?canceled=true`,
            allow_promotion_codes: true,
        });

        return NextResponse.json({ url: session.url, demo: false });
    } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
