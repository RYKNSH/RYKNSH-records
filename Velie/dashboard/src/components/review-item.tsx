interface ReviewItemProps {
    prNumber: number;
    repo: string;
    title: string;
    author: string;
    severity: "critical" | "warning" | "clean";
    createdAt: string;
}

const severityConfig = {
    critical: { dot: "bg-red-500", label: "Critical", bg: "bg-red-500/10 text-red-400" },
    warning: { dot: "bg-amber-500", label: "Warning", bg: "bg-amber-500/10 text-amber-400" },
    clean: { dot: "bg-emerald-500", label: "Clean", bg: "bg-emerald-500/10 text-emerald-400" },
};

export function ReviewItem({ prNumber, repo, title, author, severity, createdAt }: ReviewItemProps) {
    const config = severityConfig[severity];
    return (
        <div className="glass glass-hover p-4 flex items-center gap-4">
            <div className={`status-dot ${config.dot} flex-shrink-0`} />
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
            <span className={`text-[10px] font-medium px-2 py-1 rounded-full ${config.bg}`}>
                {config.label}
            </span>
        </div>
    );
}
