"use client";

import { Sidebar } from "@/components/sidebar";
import { useEffect, useState } from "react";

type SettingField =
    | { label: string; key: string; value: string; type: "select"; options: string[] }
    | { label: string; key: string; value: string; type: "text" }
    | { label: string; key: string; value: boolean; type: "toggle" }
    | { label: string; key: string; value: string; type: "readonly" };

export default function SettingsPage() {
    const [settings, setSettings] = useState<Record<string, unknown>>({});
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    useEffect(() => {
        fetch("/api/settings")
            .then((r) => r.json())
            .then(setSettings)
            .catch(() => { });
    }, []);

    function updateField(key: string, value: unknown) {
        setSettings((prev) => ({ ...prev, [key]: value }));
    }

    async function handleSave() {
        setSaving(true);
        setMessage(null);
        try {
            const res = await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });
            const data = await res.json();
            if (data.success) {
                setMessage("✅ Settings saved successfully!");
            } else {
                setMessage("❌ Failed to save settings");
            }
        } catch {
            setMessage("❌ Error saving settings");
        }
        setSaving(false);
    }

    const sections: { title: string; icon: string; fields: SettingField[] }[] = [
        {
            title: "Review Configuration",
            icon: "🔧",
            fields: [
                { label: "LLM Model", key: "llm_model", value: (settings.llm_model as string) || "claude-sonnet-4-20250514", type: "select", options: ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"] },
                { label: "Review Language", key: "review_language", value: (settings.review_language as string) || "English", type: "select", options: ["English", "Japanese", "Auto-detect"] },
                { label: "Max Diff Size", key: "max_diff_size", value: (settings.max_diff_size as string) || "60,000 chars", type: "text" },
            ],
        },
        {
            title: "Auto-Fix",
            icon: "🔧",
            fields: [
                { label: "Auto-Fix Threshold", key: "auto_fix_threshold", value: (settings.auto_fix_threshold as string) || "off", type: "select", options: ["off", "critical", "warning"] },
                { label: "Auto Suggestions", key: "auto_suggest", value: (settings.auto_suggest as boolean) ?? true, type: "toggle" },
            ],
        },
        {
            title: "Notifications",
            icon: "🔔",
            fields: [
                { label: "Email on Critical", key: "email_on_critical", value: (settings.email_on_critical as boolean) ?? true, type: "toggle" },
                { label: "Slack Integration", key: "slack_integration", value: (settings.slack_integration as boolean) ?? false, type: "toggle" },
            ],
        },
        {
            title: "GitHub App",
            icon: "🔑",
            fields: [
                { label: "App ID", key: "app_id", value: "2915193", type: "readonly" },
                { label: "Installation ID", key: "installation_id", value: "111510454", type: "readonly" },
                { label: "Permissions", key: "permissions", value: "Contents (R), Pull Requests (RW)", type: "readonly" },
            ],
        },
    ];

    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white">Settings</h2>
                    <p className="text-sm text-gray-500 mt-1">Configure your AI code review preferences</p>
                </div>

                {message && (
                    <div className="glass p-4 mb-6 border-purple-500/30">
                        <p className="text-sm text-purple-300">{message}</p>
                    </div>
                )}

                <div className="space-y-6 max-w-2xl">
                    {sections.map((section) => (
                        <div key={section.title} className="glass p-6">
                            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2 mb-6">
                                <span>{section.icon}</span>
                                {section.title}
                            </h3>

                            <div className="space-y-5">
                                {section.fields.map((field) => (
                                    <div key={field.label} className="flex items-center justify-between">
                                        <label className="text-sm text-gray-400">{field.label}</label>

                                        {field.type === "select" && (
                                            <select
                                                value={field.value}
                                                onChange={(e) => updateField(field.key, e.target.value)}
                                                className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-purple-500 focus:outline-none w-64"
                                            >
                                                {field.options.map((opt) => (
                                                    <option key={opt} value={opt}>
                                                        {opt}
                                                    </option>
                                                ))}
                                            </select>
                                        )}

                                        {field.type === "text" && (
                                            <input
                                                type="text"
                                                value={field.value}
                                                onChange={(e) => updateField(field.key, e.target.value)}
                                                className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-purple-500 focus:outline-none w-64"
                                            />
                                        )}

                                        {field.type === "toggle" && (
                                            <button
                                                onClick={() => updateField(field.key, !field.value)}
                                                className={`w-12 h-6 rounded-full relative transition-all cursor-pointer ${field.value ? "bg-purple-500" : "bg-gray-700"
                                                    }`}
                                            >
                                                <span
                                                    className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${field.value ? "left-7" : "left-1"
                                                        }`}
                                                />
                                            </button>
                                        )}

                                        {field.type === "readonly" && (
                                            <span className="text-sm text-gray-500 font-mono">{field.value}</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}

                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="w-full py-3 rounded-xl bg-purple-500 hover:bg-purple-600 text-white font-medium text-sm transition-all hover:shadow-lg hover:shadow-purple-500/20 cursor-pointer disabled:opacity-50"
                    >
                        {saving ? "Saving..." : "Save Configuration"}
                    </button>
                </div>
            </main>
        </div>
    );
}
