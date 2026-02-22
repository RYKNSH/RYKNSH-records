"use client";

import { useState } from "react";
import Link from "next/link";
import { useLocale } from "@/components/locale-context";

export default function OnboardingPage() {
    const { t } = useLocale();
    const [currentStep, setCurrentStep] = useState(0);

    const steps = [
        {
            num: 1,
            title: t("onboarding.step1Title"),
            desc: t("onboarding.step1Desc"),
            icon: "🔗",
            action: t("onboarding.step1Action"),
            detail: t("onboarding.step1Detail"),
        },
        {
            num: 2,
            title: t("onboarding.step2Title"),
            desc: t("onboarding.step2Desc"),
            icon: "📝",
            detail: t("onboarding.step2Detail"),
        },
        {
            num: 3,
            title: t("onboarding.step3Title"),
            desc: t("onboarding.step3Desc"),
            icon: "🛡️",
            action: t("onboarding.step3Action"),
            detail: t("onboarding.step3Detail"),
        },
    ];

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
                        {t("onboarding.stepOf")} {step.num} / 3
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
                                {step.action}
                            </a>
                        )}

                        {currentStep === 1 && (
                            <button
                                onClick={() => setCurrentStep(2)}
                                className="bg-purple-500 hover:bg-purple-600 text-white py-3 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/20 cursor-pointer"
                            >
                                {t("onboarding.next")}
                            </button>
                        )}

                        {currentStep === 2 && (
                            <Link
                                href="/dashboard"
                                className="bg-purple-500 hover:bg-purple-600 text-white py-3 rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-purple-500/20 block text-center"
                            >
                                {step.action}
                            </Link>
                        )}

                        {currentStep > 0 && currentStep < 2 && (
                            <button
                                onClick={() => setCurrentStep(currentStep - 1)}
                                className="text-gray-500 hover:text-gray-400 text-xs transition-colors cursor-pointer"
                            >
                                {t("onboarding.back")}
                            </button>
                        )}

                        {currentStep === 0 && (
                            <button
                                onClick={() => setCurrentStep(1)}
                                className="text-gray-600 hover:text-gray-400 text-xs transition-colors cursor-pointer"
                            >
                                {t("onboarding.alreadyInstalled")}
                            </button>
                        )}
                    </div>
                </div>

                {/* Skip */}
                <div className="text-center mt-6">
                    <Link href="/dashboard" className="text-xs text-gray-600 hover:text-gray-400 transition-colors">
                        {t("onboarding.skip")}
                    </Link>
                </div>
            </div>
        </div>
    );
}
