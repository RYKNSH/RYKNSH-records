"use client";

import { useState } from "react";

interface FixButtonProps {
    reviewId: string;
    repo: string;
    prNumber: number;
}

export function FixButton({ reviewId, repo, prNumber }: FixButtonProps) {
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [fixUrl, setFixUrl] = useState<string | null>(null);

    async function handleFix() {
        setStatus("loading");
        try {
            const res = await fetch("/api/autofix", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reviewId, repo, prNumber }),
            });
            const data = await res.json();
            if (data.success) {
                setStatus("success");
                setFixUrl(data.fix_pr_url);
            } else {
                setStatus("error");
            }
        } catch {
            setStatus("error");
        }
    }

    if (status === "success") {
        return (
            <div className="flex items-center gap-3">
                <span className="text-emerald-400 text-sm">✅ 修正PRを作成しました</span>
                {fixUrl && (
                    <a
                        href={fixUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 px-4 py-2 rounded-lg transition-all"
                    >
                        GitHubで確認 ↗
                    </a>
                )}
            </div>
        );
    }

    if (status === "error") {
        return (
            <div className="flex items-center gap-3">
                <span className="text-red-400 text-sm">修正に失敗しました</span>
                <button
                    onClick={handleFix}
                    className="text-xs bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 px-4 py-2 rounded-lg transition-all cursor-pointer"
                >
                    🔄 再試行
                </button>
            </div>
        );
    }

    return (
        <button
            onClick={handleFix}
            disabled={status === "loading"}
            className="text-sm bg-purple-500 hover:bg-purple-600 text-white px-6 py-2.5 rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/20 cursor-pointer disabled:opacity-50"
        >
            {status === "loading" ? "修正中..." : "🔧 ボタン1つで修正する"}
        </button>
    );
}
