"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { type Locale, DEFAULT_LOCALE, t as translate } from "@/lib/i18n";

interface LocaleContextType {
    locale: Locale;
    setLocale: (locale: Locale) => void;
    t: (key: Parameters<typeof translate>[0], params?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextType>({
    locale: DEFAULT_LOCALE,
    setLocale: () => { },
    t: (key) => translate(key, DEFAULT_LOCALE),
});

export function LocaleProvider({ children }: { children: ReactNode }) {
    const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

    // Load from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem("velie-locale") as Locale | null;
        if (saved && ["ja", "en", "zh"].includes(saved)) {
            setLocaleState(saved);
        } else {
            // Auto-detect from browser
            const browserLang = navigator.language.slice(0, 2);
            if (browserLang === "ja") setLocaleState("ja");
            else if (browserLang === "zh") setLocaleState("zh");
            else setLocaleState("en");
        }
    }, []);

    function setLocale(newLocale: Locale) {
        setLocaleState(newLocale);
        localStorage.setItem("velie-locale", newLocale);
    }

    function t(key: Parameters<typeof translate>[0], params?: Record<string, string | number>) {
        return translate(key, locale, params);
    }

    return (
        <LocaleContext.Provider value={{ locale, setLocale, t }}>
            {children}
        </LocaleContext.Provider>
    );
}

export function useLocale() {
    return useContext(LocaleContext);
}
