"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { useLocale } from "@/components/locale-context";

const navItems = [
    { href: "/dashboard", label: "Overview", icon: "📊" },
    { href: "/reviews", label: "Reviews", icon: "🔍" },
    { href: "/settings", label: "Settings", icon: "⚙️" },
    { href: "/billing", label: "Billing", icon: "💳" },
];

const planLabels: Record<string, string> = {
    free: "Free",
    anshin: "Starter",
    pro: "Pro",
    team: "Team",
};

interface SessionData {
    authenticated: boolean;
    user: string;
    login: string;
    avatar: string;
    plan: string;
}

export function Sidebar() {
    const pathname = usePathname();
    const { t } = useLocale();
    const [session, setSession] = useState<SessionData | null>(null);

    useEffect(() => {
        fetch("/api/session")
            .then((r) => r.json())
            .then(setSession)
            .catch(() => { });
    }, []);

    const displayName = session?.user || session?.login || "Guest";
    const initial = displayName.charAt(0).toUpperCase();
    const planLabel = planLabels[session?.plan || "free"] || "Free";

    return (
        <aside className="w-64 h-screen fixed left-0 top-0 glass border-r border-white/5 flex flex-col z-50">
            {/* Logo */}
            <div className="p-6 border-b border-white/5">
                <Link href="/">
                    <h1 className="text-2xl font-bold">
                        <span className="glow-text text-purple-400">Velie</span>
                        <span className="text-gray-500 text-sm ml-2 font-normal">CI</span>
                    </h1>
                    <p className="text-xs text-gray-500 mt-1">AI Code Review Dashboard</p>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all group ${isActive
                                ? "bg-purple-500/15 text-white border border-purple-500/20"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            <span className={`text-lg transition-transform ${isActive ? "scale-110" : "group-hover:scale-110"}`}>
                                {item.icon}
                            </span>
                            <span className="text-sm font-medium">{item.label}</span>
                            {isActive && (
                                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-400" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Language Switcher */}
            <div className="px-4 pb-2">
                <LocaleSwitcher />
            </div>

            {/* User info — dynamic from session */}
            <div className="p-4 border-t border-white/5">
                <div className="flex items-center gap-3 px-4 py-2">
                    {session?.avatar ? (
                        <img
                            src={session.avatar}
                            alt={displayName}
                            className="w-8 h-8 rounded-full"
                        />
                    ) : (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                            <span className="text-white text-xs font-bold">{initial}</span>
                        </div>
                    )}
                    <div className="min-w-0">
                        <p className="text-xs font-medium text-gray-300 truncate">{displayName}</p>
                        <p className="text-[10px] text-gray-600">{planLabel} Plan</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
