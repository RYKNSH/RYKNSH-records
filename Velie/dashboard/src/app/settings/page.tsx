import { Sidebar } from "@/components/sidebar";

type SettingField =
    | { label: string; value: string; type: "select"; options: string[] }
    | { label: string; value: string; type: "text" }
    | { label: string; value: boolean; type: "toggle" }
    | { label: string; value: string; type: "readonly" };

const settingSections: { title: string; icon: string; fields: SettingField[] }[] = [
    {
        title: "Review Configuration",
        icon: "🔧",
        fields: [
            { label: "LLM Model", value: "claude-sonnet-4-20250514", type: "select", options: ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"] },
            { label: "Review Language", value: "English", type: "select", options: ["English", "Japanese", "Auto-detect"] },
            { label: "Max Diff Size", value: "60,000 chars", type: "text" },
        ],
    },
    {
        title: "Notifications",
        icon: "🔔",
        fields: [
            { label: "Email on Critical", value: true, type: "toggle" },
            { label: "Slack Integration", value: false, type: "toggle" },
        ],
    },
    {
        title: "GitHub App",
        icon: "🔑",
        fields: [
            { label: "App ID", value: "2915193", type: "readonly" },
            { label: "Installation ID", value: "111510454", type: "readonly" },
            { label: "Permissions", value: "Contents (R), Pull Requests (RW)", type: "readonly" },
        ],
    },
];

export default function SettingsPage() {
    return (
        <div className="flex min-h-screen">
            <Sidebar />

            <main className="flex-1 ml-64 p-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white">Settings</h2>
                    <p className="text-sm text-gray-500 mt-1">Configure your AI code review preferences</p>
                </div>

                <div className="space-y-6 max-w-2xl">
                    {settingSections.map((section) => (
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
                                            <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-purple-500 focus:outline-none w-64">
                                                {field.options.map((opt) => (
                                                    <option key={opt} value={opt} selected={opt === field.value}>
                                                        {opt}
                                                    </option>
                                                ))}
                                            </select>
                                        )}

                                        {field.type === "text" && (
                                            <input
                                                type="text"
                                                defaultValue={field.value}
                                                className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-purple-500 focus:outline-none w-64"
                                            />
                                        )}

                                        {field.type === "toggle" && (
                                            <button
                                                className={`w-12 h-6 rounded-full relative transition-all ${field.value ? "bg-purple-500" : "bg-gray-700"
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

                    {/* Save button */}
                    <button className="w-full py-3 rounded-xl bg-purple-500 hover:bg-purple-600 text-white font-medium text-sm transition-all hover:shadow-lg hover:shadow-purple-500/20">
                        Save Configuration
                    </button>
                </div>
            </main>
        </div>
    );
}
