import { NextResponse } from "next/server";

/**
 * POST /api/billing/checkout — Create Stripe Checkout session.
 * In production, this connects to Stripe API.
 */
export async function POST(request: Request) {
    const { plan } = await request.json();

    const stripeKey = process.env.STRIPE_SECRET_KEY;

    if (!stripeKey) {
        // Demo mode: redirect to billing with message
        return NextResponse.json({
            url: "/billing?upgraded=demo",
            demo: true,
        });
    }

    // TODO: Real Stripe implementation
    // const stripe = new Stripe(stripeKey);
    // const session = await stripe.checkout.sessions.create({
    //   mode: "subscription",
    //   line_items: [{ price: PRICE_IDS[plan], quantity: 1 }],
    //   success_url: `${process.env.NEXT_PUBLIC_SITE_URL}/billing?success=true`,
    //   cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL}/billing?canceled=true`,
    // });
    // return NextResponse.json({ url: session.url });

    return NextResponse.json({
        url: `/billing?plan=${plan}&checkout=pending`,
        demo: true,
    });
}
