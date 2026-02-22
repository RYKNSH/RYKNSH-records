"use client";

import { useLocale } from "@/components/locale-context";
import { SUPPORTED_LOCALES, type Locale } from "@/lib/i18n";
import { useState } from "react";

export function LocaleSwitcher() {
    const { locale, setLocale } = useLocale();
    const [open, setOpen] = useState(false);

    const current = SUPPORTED_LOCALES.find((l) => l.code === locale) || SUPPORTED_LOCALES[0];

    return (
        <div className="relative">
            <button
                onClick={() => setOpen(!open)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-sm text-gray-300 transition-all cursor-pointer"
            >
                <span>{current.flag}</span>
                <span className="text-xs">{current.label}</span>
                <span className="text-[10px] text-gray-600">▼</span>
            </button>

            {open && (
                <div className="absolute bottom-full left-0 mb-2 bg-gray-900 border border-white/10 rounded-xl overflow-hidden shadow-2xl z-50 min-w-[140px]">
                    {SUPPORTED_LOCALES.map((l) => (
                        <button
                            key={l.code}
                            onClick={() => {
                                setLocale(l.code as Locale);
                                setOpen(false);
                            }}
                            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-all cursor-pointer ${l.code === locale
                                    ? "bg-purple-500/20 text-purple-300"
                                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                                }`}
                        >
                            <span>{l.flag}</span>
                            <span>{l.label}</span>
                            {l.code === locale && <span className="ml-auto text-purple-400">✓</span>}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
