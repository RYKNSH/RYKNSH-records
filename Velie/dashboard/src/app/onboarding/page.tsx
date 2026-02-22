"use client";

import { useState } from "react";
import Link from "next/link";

const steps = [
    {
        num: 1,
        title: "GitHubと繋ぐ",
        desc: "ボタン1つでVelieをリポジトリに接続。30秒で完了します。",
        icon: "🔗",
        action: "GitHub Appをインストール",
        detail: "Velieは読み取り専用アクセスのみ。コードを書き換えることはありません。",
    },
    {
        num: 2,
        title: "Pull Requestを出す",
        desc: "いつも通りコードを書いてPRを出すだけ。特別な操作は不要です。",
        icon: "📝",
        action: "PRを作成する",
        detail: "Cursor、Copilot、v0、bolt.new — どんなツールで書いたコードでもOK。",
    },
    {
        num: 3,
        title: "安心して公開",
        desc: "VelieがAIで自動チェック。安全スコア○△×で結果が一目でわかります。",
        icon: "🛡️",
        action: "ダッシュボードを見る",
        detail: "問題が見つかったら「🔧 修正する」ボタン1つで自動修正。",
    },
];

export default function OnboardingPage() {
    const [currentStep, setCurrentStep] = useState(0);
    const step = steps[currentStep];

    return (
        <div className="min-h-screen flex items-center justify-center">
            {/* Background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/8 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 w-full max-w-lg px-6">
                {/* Progress bar */}
                <div className="flex items-center gap-2 mb-10">
                    {steps.map((s, i) => (
                        <div key={s.num} className="flex items-center flex-1">
                            <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${i <= currentStep
                                        ? "bg-purple-500 text-white"
                                        : "bg-white/5 text-gray-600 border border-white/10"
                                    }`}
                            >
                                {i < currentStep ? "✓" : s.num}
                            </div>
                            {i < steps.length - 1 && (
                                <div
                                    className={`flex-1 h-0.5 mx-2 transition-all ${i < currentStep ? "bg-purple-500" : "bg-white/10"
                                        }`}
                                />
                            )}
                        </div>
                    ))}
                </div>

                {/* Step content */}
                <div className="glass p-8 text-center">
                    <span className="text-5xl block mb-4">{step.icon}</span>
                    <div className="text-xs text-purple-400 font-medium mb-2">
                        ステップ {step.num} / 3
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-3">{step.title}</h2>
                    <p className="text-gray-400 text-sm mb-6">{step.desc}</p>

                    <div className="bg-white/5 rounded-xl p-4 mb-6">
                        <p className="text-xs text-gray-500">{step.detail}</p>
                    </div>

                    <div className="flex flex-col gap-3">
                        {currentStep === 0 && (
                            <a
                                href="https://github.com/apps/velie-qa-agent/installations/new"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="bg-purple-500 hover:bg-purple-600 text-white py-3 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/20 block"
                                onClick={() => setTimeout(() => setCurrentStep(1), 1000)}
                            >
                                {step.action} →
                            </a>
                        )}

                        {currentStep === 1 && (
                            <button
                                onClick={() => setCurrentStep(2)}
                                className="bg-purple-500 hover:bg-purple-600 text-white py-3 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/20 cursor-pointer"
                            >
                                完了、次へ →
                            </button>
                        )}

                        {currentStep === 2 && (
                            <Link
                                href="/dashboard"
                                className="bg-purple-500 hover:bg-purple-600 text-white py-3 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/20 block text-center"
                            >
                                ダッシュボードへ →
                            </Link>
                        )}

                        {currentStep > 0 && currentStep < 2 && (
                            <button
                                onClick={() => setCurrentStep(currentStep - 1)}
                                className="text-gray-500 hover:text-gray-400 text-xs transition-colors cursor-pointer"
                            >
                                ← 戻る
                            </button>
                        )}

                        {currentStep === 0 && (
                            <button
                                onClick={() => setCurrentStep(1)}
                                className="text-gray-600 hover:text-gray-400 text-xs transition-colors cursor-pointer"
                            >
                                すでにインストール済み →
                            </button>
                        )}
                    </div>
                </div>

                {/* Skip */}
                <div className="text-center mt-6">
                    <Link href="/dashboard" className="text-xs text-gray-600 hover:text-gray-400 transition-colors">
                        スキップしてダッシュボードへ
                    </Link>
                </div>
            </div>
        </div>
    );
}
