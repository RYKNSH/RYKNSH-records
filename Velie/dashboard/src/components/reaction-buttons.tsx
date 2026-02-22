"use client";

import { useState } from "react";

type ReactionState = "idle" | "helpful" | "not_helpful";

export function ReactionButtons({ reviewId }: { reviewId: string }) {
    const [state, setState] = useState<ReactionState>("idle");
    const [sending, setSending] = useState(false);

    async function handleReaction(reaction: "helpful" | "not_helpful") {
        if (state !== "idle" || sending) return;
        setSending(true);

        try {
            const res = await fetch("/api/reactions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ review_id: reviewId, reaction }),
            });

            if (res.ok) {
                setState(reaction);
            }
        } catch {
            // silently fail
        } finally {
            setSending(false);
        }
    }

    if (state !== "idle") {
        return (
            <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>{state === "helpful" ? "👍" : "👎"}</span>
                <span>フィードバックありがとうございます</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600">このレビューは役に立ちましたか？</span>
            <button
                onClick={() => handleReaction("helpful")}
                disabled={sending}
                className="text-lg hover:scale-125 transition-transform cursor-pointer disabled:opacity-50"
                title="役に立った"
            >
                👍
            </button>
            <button
                onClick={() => handleReaction("not_helpful")}
                disabled={sending}
                className="text-lg hover:scale-125 transition-transform cursor-pointer disabled:opacity-50"
                title="役に立たなかった"
            >
                👎
            </button>
        </div>
    );
}
