import Link from "next/link";

const navItems = [
    { href: "/", label: "Overview", icon: "📊" },
    { href: "/reviews", label: "Reviews", icon: "🔍" },
    { href: "/settings", label: "Settings", icon: "⚙️" },
    { href: "/billing", label: "Billing", icon: "💳" },
];

export function Sidebar() {
    return (
        <aside className="w-64 h-screen fixed left-0 top-0 glass border-r border-white/5 flex flex-col">
            {/* Logo */}
            <div className="p-6 border-b border-white/5">
                <h1 className="text-2xl font-bold">
                    <span className="glow-text text-purple-400">Velie</span>
                    <span className="text-gray-500 text-sm ml-2 font-normal">CI</span>
                </h1>
                <p className="text-xs text-gray-500 mt-1">AI Code Review Dashboard</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1">
                {navItems.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all group"
                    >
                        <span className="text-lg group-hover:scale-110 transition-transform">
                            {item.icon}
                        </span>
                        <span className="text-sm font-medium">{item.label}</span>
                    </Link>
                ))}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-white/5">
                <div className="flex items-center gap-3 px-4 py-2">
                    <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                        <span className="text-purple-400 text-sm">R</span>
                    </div>
                    <div>
                        <p className="text-xs font-medium text-gray-300">RYKNSH records</p>
                        <p className="text-[10px] text-gray-600">Free Plan</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
