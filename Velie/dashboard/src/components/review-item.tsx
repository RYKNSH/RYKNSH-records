import Link from "next/link";

interface ReviewItemProps {
    id?: string;
    prNumber: number;
    repo: string;
    title: string;
    author: string;
    severity: "critical" | "warning" | "clean";
    createdAt: string;
}

const safetyConfig = {
    critical: { symbol: "×", label: "危険", bg: "bg-red-500/10 text-red-400", border: "border-l-red-500/60" },
    warning: { symbol: "△", label: "注意", bg: "bg-amber-500/10 text-amber-400", border: "border-l-amber-500/60" },
    clean: { symbol: "○", label: "安全", bg: "bg-emerald-500/10 text-emerald-400", border: "border-l-emerald-500/60" },
};

export function ReviewItem({ id, prNumber, repo, title, author, severity, createdAt }: ReviewItemProps) {
    const config = safetyConfig[severity];
    const content = (
        <div className={`glass glass-hover p-4 flex items-center gap-4 cursor-pointer border-l-4 ${config.border}`}>
            <span className="text-2xl flex-shrink-0">{config.symbol}</span>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white truncate">{title}</span>
                    <span className="text-xs text-gray-600">#{prNumber}</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-500">{repo}</span>
                    <span className="text-xs text-gray-700">·</span>
                    <span className="text-xs text-gray-500">{author}</span>
                    <span className="text-xs text-gray-700">·</span>
                    <span className="text-xs text-gray-600">{createdAt}</span>
                </div>
            </div>
            <span className={`text-[10px] font-medium px-2.5 py-1 rounded-full ${config.bg}`}>
                {config.symbol} {config.label}
            </span>
            <span className="text-gray-600 text-xs">→</span>
        </div>
    );

    if (id) {
        return <Link href={`/reviews/${encodeURIComponent(id)}`}>{content}</Link>;
    }
    return content;
}
