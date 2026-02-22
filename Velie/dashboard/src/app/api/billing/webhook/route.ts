import { NextResponse, type NextRequest } from "next/server";

/**
 * POST /api/billing/webhook — Handle Stripe webhook events.
 * Updates tenant plan on successful subscription.
 */
export async function POST(request: NextRequest) {
    const stripeKey = process.env.STRIPE_SECRET_KEY;
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

    if (!stripeKey || !webhookSecret) {
        return NextResponse.json({ received: true, demo: true });
    }

    try {
        const Stripe = (await import("stripe")).default;
        const stripe = new Stripe(stripeKey);

        const body = await request.text();
        const sig = request.headers.get("stripe-signature");

        if (!sig) {
            return NextResponse.json({ error: "Missing signature" }, { status: 400 });
        }

        const event = stripe.webhooks.constructEvent(body, sig, webhookSecret);

        switch (event.type) {
            case "checkout.session.completed": {
                const session = event.data.object;
                const customerId = session.customer as string;
                // Update tenant plan via Velie backend
                const baseUrl = process.env.VELIE_API_URL || "http://localhost:8000";
                await fetch(`${baseUrl}/api/plan/upgrade`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        stripe_customer_id: customerId,
                        subscription_id: session.subscription,
                    }),
                });
                break;
            }
            case "customer.subscription.deleted": {
                const sub = event.data.object;
                const baseUrl = process.env.VELIE_API_URL || "http://localhost:8000";
                await fetch(`${baseUrl}/api/plan/downgrade`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        stripe_customer_id: sub.customer,
                    }),
                });
                break;
            }
        }

        return NextResponse.json({ received: true });
    } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return NextResponse.json({ error: message }, { status: 400 });
    }
}
