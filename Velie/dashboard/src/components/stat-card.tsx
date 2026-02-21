interface StatCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    trend?: { value: number; label: string };
    icon: string;
    color?: "purple" | "green" | "blue" | "amber";
}

const colorMap = {
    purple: "from-purple-500/20 to-purple-600/5 border-purple-500/20",
    green: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20",
    blue: "from-blue-500/20 to-blue-600/5 border-blue-500/20",
    amber: "from-amber-500/20 to-amber-600/5 border-amber-500/20",
};

export function StatCard({ title, value, subtitle, trend, icon, color = "purple" }: StatCardProps) {
    return (
        <div className={`glass glass-hover p-6 bg-gradient-to-br ${colorMap[color]}`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">{title}</p>
                    <p className="text-3xl font-bold mt-2 text-white">{value}</p>
                    {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
                    {trend && (
                        <p className={`text-xs mt-2 ${trend.value >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {trend.value >= 0 ? "↑" : "↓"} {Math.abs(trend.value)}% {trend.label}
                        </p>
                    )}
                </div>
                <span className="text-3xl opacity-60">{icon}</span>
            </div>
        </div>
    );
}
