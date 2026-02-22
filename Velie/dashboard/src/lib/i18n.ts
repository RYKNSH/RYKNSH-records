/**
 * Velie i18n — Multi-language support.
 *
 * Supported locales: ja (日本語), en (English), zh (中文)
 * Default: ja (Japanese market first → global expansion)
 */

export type Locale = "ja" | "en" | "zh";

export const SUPPORTED_LOCALES: { code: Locale; label: string; flag: string }[] = [
    { code: "ja", label: "日本語", flag: "🇯🇵" },
    { code: "en", label: "English", flag: "🇺🇸" },
    { code: "zh", label: "中文", flag: "🇨🇳" },
];

export const DEFAULT_LOCALE: Locale = "ja";

// ---------------------------------------------------------------------------
// Translation dictionary
// ---------------------------------------------------------------------------

type TranslationKeys = {
    // Dashboard
    "dashboard.title": string;
    "dashboard.subtitle": string;
    "dashboard.totalReviews": string;
    "dashboard.safetyScore": string;
    "dashboard.satisfaction": string;
    "dashboard.dangerDetection": string;
    "dashboard.thisWeek": string;
    "dashboard.noData": string;
    "dashboard.noReview": string;
    "dashboard.noRating": string;
    "dashboard.detectionRate": string;
    "dashboard.acceptanceRate": string;
    "dashboard.ratings": string;
    "dashboard.recentReviews": string;
    "dashboard.viewAll": string;
    "dashboard.welcome": string;
    "dashboard.welcomeDesc": string;
    "dashboard.step1Title": string;
    "dashboard.step1Desc": string;
    "dashboard.step2Title": string;
    "dashboard.step2Desc": string;
    "dashboard.step3Title": string;
    "dashboard.step3Desc": string;
    "dashboard.getStarted": string;
    "dashboard.systemStatus": string;
    "dashboard.webhookServer": string;
    "dashboard.connected": string;
    "dashboard.recentErrors": string;
    "dashboard.active": string;
    // Health status
    "health.healthy": string;
    "health.warning": string;
    "health.degraded": string;
    "health.unknown": string;
    // Settings
    "settings.title": string;
    "settings.subtitle": string;
    "settings.reviewConfig": string;
    "settings.aiModel": string;
    "settings.reviewLanguage": string;
    "settings.maxDiffSize": string;
    "settings.autoFix": string;
    "settings.autoFixTrigger": string;
    "settings.autoSuggest": string;
    "settings.notifications": string;
    "settings.emailOnCritical": string;
    "settings.slackIntegration": string;
    "settings.permissions": string;
    "settings.save": string;
    "settings.saving": string;
    "settings.saved": string;
    "settings.saveFailed": string;
    "settings.saveError": string;
    // Billing
    "billing.title": string;
    "billing.subtitle": string;
    "billing.currentUsage": string;
    "billing.reviews": string;
    "billing.remaining": string;
    "billing.limitReached": string;
    "billing.currentPlan": string;
    "billing.upgrade": string;
    "billing.processing": string;
    "billing.recommended": string;
    "billing.perMonth": string;
    "billing.upgraded": string;
    "billing.canceled": string;
    "billing.demoMode": string;
    "billing.checkoutError": string;
    // Plans
    "plan.free": string;
    "plan.anshin": string;
    "plan.pro": string;
    "plan.team": string;
    // Plan features
    "feature.reviewsPerMonth": string;
    "feature.repos": string;
    "feature.unlimitedReviews": string;
    "feature.unlimitedRepos": string;
    "feature.unlimitedAll": string;
    "feature.communitySupport": string;
    "feature.emailSupport": string;
    "feature.prioritySupport": string;
    "feature.dedicatedSupport": string;
    "feature.japaneseReview": string;
    "feature.customPrompts": string;
    "feature.oneClickFix": string;
    "feature.ssoSaml": string;
    "feature.onPremise": string;
    // Review detail
    "review.backToList": string;
    "review.notFound": string;
    "review.viewOnGithub": string;
    "review.fixSection": string;
    "review.fixDesc": string;
    "review.reactionAsk": string;
    "review.reactionThanks": string;
    // Safety score
    "safety.critical": string;
    "safety.warning": string;
    "safety.clean": string;
    // Onboarding
    "onboarding.step1Title": string;
    "onboarding.step1Desc": string;
    "onboarding.step1Detail": string;
    "onboarding.step1Action": string;
    "onboarding.step2Title": string;
    "onboarding.step2Desc": string;
    "onboarding.step2Detail": string;
    "onboarding.step3Title": string;
    "onboarding.step3Desc": string;
    "onboarding.step3Detail": string;
    "onboarding.step3Action": string;
    "onboarding.alreadyInstalled": string;
    "onboarding.next": string;
    "onboarding.back": string;
    "onboarding.skip": string;
    "onboarding.stepOf": string;
    // Common
    "common.loading": string;
};

const translations: Record<Locale, TranslationKeys> = {
    ja: {
        "dashboard.title": "ダッシュボード",
        "dashboard.subtitle": "Velieのレビュー状況をひと目で確認",
        "dashboard.totalReviews": "レビュー総数",
        "dashboard.safetyScore": "安全スコア",
        "dashboard.satisfaction": "満足度",
        "dashboard.dangerDetection": "危険検出",
        "dashboard.thisWeek": "今週",
        "dashboard.noData": "データなし",
        "dashboard.noReview": "レビューなし",
        "dashboard.noRating": "評価なし",
        "dashboard.detectionRate": "検出率",
        "dashboard.acceptanceRate": "承認率",
        "dashboard.ratings": "件の評価",
        "dashboard.recentReviews": "最近のレビュー",
        "dashboard.viewAll": "すべて見る →",
        "dashboard.welcome": "Velieへようこそ！",
        "dashboard.welcomeDesc": "AIがあなたのコードを守ります。3ステップで始めましょう：",
        "dashboard.step1Title": "GitHubと繋ぐ",
        "dashboard.step1Desc": "リポジトリをVelieに接続します",
        "dashboard.step2Title": "Pull Requestを出す",
        "dashboard.step2Desc": "Velieが自動でレビューします",
        "dashboard.step3Title": "安全スコアを確認",
        "dashboard.step3Desc": "○△×で結果がひと目でわかります",
        "dashboard.getStarted": "今すぐ始める →",
        "dashboard.systemStatus": "システムステータス",
        "dashboard.webhookServer": "Webhookサーバー",
        "dashboard.connected": "接続済み",
        "dashboard.recentErrors": "最近のエラー",
        "dashboard.active": "稼働中",
        "health.healthy": "正常",
        "health.warning": "注意",
        "health.degraded": "異常",
        "health.unknown": "未接続",
        "settings.title": "設定",
        "settings.subtitle": "AIコードレビューの動作をカスタマイズ",
        "settings.reviewConfig": "レビュー設定",
        "settings.aiModel": "AIモデル",
        "settings.reviewLanguage": "レビュー言語",
        "settings.maxDiffSize": "最大diffサイズ",
        "settings.autoFix": "自動修正",
        "settings.autoFixTrigger": "自動修正トリガー",
        "settings.autoSuggest": "修正提案を自動生成",
        "settings.notifications": "通知",
        "settings.emailOnCritical": "危険検出時にメール通知",
        "settings.slackIntegration": "Slack連携",
        "settings.permissions": "権限",
        "settings.save": "設定を保存",
        "settings.saving": "保存中...",
        "settings.saved": "✅ 設定を保存しました",
        "settings.saveFailed": "❌ 保存に失敗しました",
        "settings.saveError": "❌ エラーが発生しました",
        "billing.title": "料金プラン",
        "billing.subtitle": "プランの管理と利用状況の確認",
        "billing.currentUsage": "今月の利用状況",
        "billing.reviews": "レビュー",
        "billing.remaining": "残り",
        "billing.limitReached": "⚠️ 上限に達しました — プランをアップグレードしてください",
        "billing.currentPlan": "現在のプラン",
        "billing.upgrade": "アップグレード",
        "billing.processing": "処理中...",
        "billing.recommended": "おすすめ",
        "billing.perMonth": "/月",
        "billing.upgraded": "プランにアップグレードしました！",
        "billing.canceled": "支払いがキャンセルされました。いつでもアップグレードできます。",
        "billing.demoMode": "🎉 デモモード — Stripe連携は本番環境で有効になります",
        "billing.checkoutError": "❌ チェックアウトセッションの作成に失敗しました",
        "plan.free": "無料プラン",
        "plan.anshin": "あんしんプラン",
        "plan.pro": "プロプラン",
        "plan.team": "チームプラン",
        "feature.reviewsPerMonth": "月{n}回レビュー",
        "feature.repos": "リポジトリ{n}つ",
        "feature.unlimitedReviews": "無制限レビュー",
        "feature.unlimitedRepos": "リポジトリ無制限",
        "feature.unlimitedAll": "無制限すべて",
        "feature.communitySupport": "コミュニティサポート",
        "feature.emailSupport": "メールサポート",
        "feature.prioritySupport": "優先サポート",
        "feature.dedicatedSupport": "専任サポート",
        "feature.japaneseReview": "日本語レビュー",
        "feature.customPrompts": "カスタムプロンプト",
        "feature.oneClickFix": "ワンクリック修正",
        "feature.ssoSaml": "SSO / SAML",
        "feature.onPremise": "オンプレミス対応",
        "review.backToList": "← レビュー一覧に戻る",
        "review.notFound": "レビューが見つかりません",
        "review.viewOnGithub": "GitHubで見る ↗",
        "review.fixSection": "問題を修正する",
        "review.fixDesc": "Velieが自動で修正PRを作成します",
        "review.reactionAsk": "このレビューは役に立ちましたか？",
        "review.reactionThanks": "フィードバックありがとうございます",
        "safety.critical": "危険",
        "safety.warning": "注意",
        "safety.clean": "安全",
        "onboarding.step1Title": "GitHubと繋ぐ",
        "onboarding.step1Desc": "ボタン1つでVelieをリポジトリに接続。30秒で完了します。",
        "onboarding.step1Detail": "Velieは読み取り専用アクセスのみ。コードを書き換えることはありません。",
        "onboarding.step1Action": "GitHub Appをインストール →",
        "onboarding.step2Title": "Pull Requestを出す",
        "onboarding.step2Desc": "いつも通りコードを書いてPRを出すだけ。特別な操作は不要です。",
        "onboarding.step2Detail": "Cursor、Copilot、v0、bolt.new — どんなツールで書いたコードでもOK。",
        "onboarding.step3Title": "安心して公開",
        "onboarding.step3Desc": "VelieがAIで自動チェック。安全スコア○△×で結果が一目でわかります。",
        "onboarding.step3Detail": "問題が見つかったら「🔧 修正する」ボタン1つで自動修正。",
        "onboarding.step3Action": "ダッシュボードへ →",
        "onboarding.alreadyInstalled": "すでにインストール済み →",
        "onboarding.next": "完了、次へ →",
        "onboarding.back": "← 戻る",
        "onboarding.skip": "スキップしてダッシュボードへ",
        "onboarding.stepOf": "ステップ",
        "common.loading": "読み込み中...",
    },
    en: {
        "dashboard.title": "Dashboard",
        "dashboard.subtitle": "AI-powered code review insights at a glance",
        "dashboard.totalReviews": "Total Reviews",
        "dashboard.safetyScore": "Safety Score",
        "dashboard.satisfaction": "Satisfaction",
        "dashboard.dangerDetection": "Critical Issues",
        "dashboard.thisWeek": "this week",
        "dashboard.noData": "No data",
        "dashboard.noReview": "No reviews",
        "dashboard.noRating": "No ratings",
        "dashboard.detectionRate": "detection rate",
        "dashboard.acceptanceRate": "acceptance",
        "dashboard.ratings": "ratings",
        "dashboard.recentReviews": "Recent Reviews",
        "dashboard.viewAll": "View all →",
        "dashboard.welcome": "Welcome to Velie!",
        "dashboard.welcomeDesc": "AI protects your code. Get started in 3 steps:",
        "dashboard.step1Title": "Connect GitHub",
        "dashboard.step1Desc": "Connect your repositories to Velie",
        "dashboard.step2Title": "Open a Pull Request",
        "dashboard.step2Desc": "Velie reviews your code automatically",
        "dashboard.step3Title": "Check Safety Score",
        "dashboard.step3Desc": "See results at a glance with ○△× scores",
        "dashboard.getStarted": "Get Started →",
        "dashboard.systemStatus": "System Status",
        "dashboard.webhookServer": "Webhook Server",
        "dashboard.connected": "Connected",
        "dashboard.recentErrors": "recent errors",
        "dashboard.active": "Active",
        "health.healthy": "Operational",
        "health.warning": "Warning",
        "health.degraded": "Degraded",
        "health.unknown": "Unknown",
        "settings.title": "Settings",
        "settings.subtitle": "Configure your AI code review preferences",
        "settings.reviewConfig": "Review Configuration",
        "settings.aiModel": "AI Model",
        "settings.reviewLanguage": "Review Language",
        "settings.maxDiffSize": "Max Diff Size",
        "settings.autoFix": "Auto-Fix",
        "settings.autoFixTrigger": "Auto-Fix Trigger",
        "settings.autoSuggest": "Auto-generate Suggestions",
        "settings.notifications": "Notifications",
        "settings.emailOnCritical": "Email on Critical Detection",
        "settings.slackIntegration": "Slack Integration",
        "settings.permissions": "Permissions",
        "settings.save": "Save Configuration",
        "settings.saving": "Saving...",
        "settings.saved": "✅ Settings saved successfully",
        "settings.saveFailed": "❌ Failed to save settings",
        "settings.saveError": "❌ Error saving settings",
        "billing.title": "Pricing Plans",
        "billing.subtitle": "Manage your subscription and usage",
        "billing.currentUsage": "Current Usage",
        "billing.reviews": "reviews",
        "billing.remaining": "remaining",
        "billing.limitReached": "⚠️ Limit reached — upgrade your plan",
        "billing.currentPlan": "Current Plan",
        "billing.upgrade": "Upgrade",
        "billing.processing": "Processing...",
        "billing.recommended": "Recommended",
        "billing.perMonth": "/mo",
        "billing.upgraded": "plan upgraded!",
        "billing.canceled": "Payment canceled. You can upgrade anytime.",
        "billing.demoMode": "🎉 Demo mode — Stripe integration available in production",
        "billing.checkoutError": "❌ Failed to create checkout session",
        "plan.free": "Free",
        "plan.anshin": "Starter",
        "plan.pro": "Pro",
        "plan.team": "Team",
        "feature.reviewsPerMonth": "{n} reviews/month",
        "feature.repos": "{n} repositories",
        "feature.unlimitedReviews": "Unlimited reviews",
        "feature.unlimitedRepos": "Unlimited repositories",
        "feature.unlimitedAll": "Unlimited everything",
        "feature.communitySupport": "Community support",
        "feature.emailSupport": "Email support",
        "feature.prioritySupport": "Priority support",
        "feature.dedicatedSupport": "Dedicated support",
        "feature.japaneseReview": "Japanese reviews",
        "feature.customPrompts": "Custom prompts",
        "feature.oneClickFix": "One-click fix",
        "feature.ssoSaml": "SSO / SAML",
        "feature.onPremise": "On-premise deployment",
        "review.backToList": "← Back to reviews",
        "review.notFound": "Review not found",
        "review.viewOnGithub": "View on GitHub ↗",
        "review.fixSection": "Fix Issues",
        "review.fixDesc": "Velie will auto-create a fix PR",
        "review.reactionAsk": "Was this review helpful?",
        "review.reactionThanks": "Thanks for your feedback",
        "safety.critical": "Critical",
        "safety.warning": "Warning",
        "safety.clean": "Clean",
        "onboarding.step1Title": "Connect GitHub",
        "onboarding.step1Desc": "Connect Velie to your repository with one click. Done in 30 seconds.",
        "onboarding.step1Detail": "Velie uses read-only access. It never modifies your code.",
        "onboarding.step1Action": "Install GitHub App →",
        "onboarding.step2Title": "Open a Pull Request",
        "onboarding.step2Desc": "Write code as usual and open a PR. No special setup needed.",
        "onboarding.step2Detail": "Cursor, Copilot, v0, bolt.new — any tool works.",
        "onboarding.step3Title": "Ship with Confidence",
        "onboarding.step3Desc": "Velie auto-checks with AI. See results instantly with ○△× safety scores.",
        "onboarding.step3Detail": "Found an issue? One click to auto-fix with 🔧 button.",
        "onboarding.step3Action": "Go to Dashboard →",
        "onboarding.alreadyInstalled": "Already installed →",
        "onboarding.next": "Done, next →",
        "onboarding.back": "← Back",
        "onboarding.skip": "Skip to dashboard",
        "onboarding.stepOf": "Step",
        "common.loading": "Loading...",
    },
    zh: {
        "dashboard.title": "仪表盘",
        "dashboard.subtitle": "AI代码审查概览一目了然",
        "dashboard.totalReviews": "审查总数",
        "dashboard.safetyScore": "安全评分",
        "dashboard.satisfaction": "满意度",
        "dashboard.dangerDetection": "危险检测",
        "dashboard.thisWeek": "本周",
        "dashboard.noData": "暂无数据",
        "dashboard.noReview": "暂无审查",
        "dashboard.noRating": "暂无评价",
        "dashboard.detectionRate": "检出率",
        "dashboard.acceptanceRate": "通过率",
        "dashboard.ratings": "条评价",
        "dashboard.recentReviews": "最近审查",
        "dashboard.viewAll": "查看全部 →",
        "dashboard.welcome": "欢迎使用Velie！",
        "dashboard.welcomeDesc": "AI守护你的代码。3步开始：",
        "dashboard.step1Title": "连接GitHub",
        "dashboard.step1Desc": "将你的仓库连接到Velie",
        "dashboard.step2Title": "创建Pull Request",
        "dashboard.step2Desc": "Velie自动审查你的代码",
        "dashboard.step3Title": "查看安全评分",
        "dashboard.step3Desc": "○△×一眼看出结果",
        "dashboard.getStarted": "立即开始 →",
        "dashboard.systemStatus": "系统状态",
        "dashboard.webhookServer": "Webhook服务器",
        "dashboard.connected": "已连接",
        "dashboard.recentErrors": "最近错误",
        "dashboard.active": "运行中",
        "health.healthy": "正常",
        "health.warning": "警告",
        "health.degraded": "异常",
        "health.unknown": "未连接",
        "settings.title": "设置",
        "settings.subtitle": "自定义AI代码审查行为",
        "settings.reviewConfig": "审查配置",
        "settings.aiModel": "AI模型",
        "settings.reviewLanguage": "审查语言",
        "settings.maxDiffSize": "最大diff大小",
        "settings.autoFix": "自动修复",
        "settings.autoFixTrigger": "自动修复触发",
        "settings.autoSuggest": "自动生成修复建议",
        "settings.notifications": "通知",
        "settings.emailOnCritical": "检测到危险时邮件通知",
        "settings.slackIntegration": "Slack集成",
        "settings.permissions": "权限",
        "settings.save": "保存设置",
        "settings.saving": "保存中...",
        "settings.saved": "✅ 设置已保存",
        "settings.saveFailed": "❌ 保存失败",
        "settings.saveError": "❌ 发生错误",
        "billing.title": "定价方案",
        "billing.subtitle": "管理订阅和使用情况",
        "billing.currentUsage": "本月使用量",
        "billing.reviews": "次审查",
        "billing.remaining": "剩余",
        "billing.limitReached": "⚠️ 已达上限 — 请升级方案",
        "billing.currentPlan": "当前方案",
        "billing.upgrade": "升级",
        "billing.processing": "处理中...",
        "billing.recommended": "推荐",
        "billing.perMonth": "/月",
        "billing.upgraded": "方案已升级！",
        "billing.canceled": "付款已取消。你可以随时升级。",
        "billing.demoMode": "🎉 演示模式 — Stripe集成将在生产环境中启用",
        "billing.checkoutError": "❌ 创建结账会话失败",
        "plan.free": "免费版",
        "plan.anshin": "入门版",
        "plan.pro": "专业版",
        "plan.team": "团队版",
        "feature.reviewsPerMonth": "每月{n}次审查",
        "feature.repos": "{n}个仓库",
        "feature.unlimitedReviews": "无限审查",
        "feature.unlimitedRepos": "无限仓库",
        "feature.unlimitedAll": "全部无限",
        "feature.communitySupport": "社区支持",
        "feature.emailSupport": "邮件支持",
        "feature.prioritySupport": "优先支持",
        "feature.dedicatedSupport": "专属支持",
        "feature.japaneseReview": "日语审查",
        "feature.customPrompts": "自定义提示",
        "feature.oneClickFix": "一键修复",
        "feature.ssoSaml": "SSO / SAML",
        "feature.onPremise": "私有部署",
        "review.backToList": "← 返回审查列表",
        "review.notFound": "未找到审查",
        "review.viewOnGithub": "在GitHub查看 ↗",
        "review.fixSection": "修复问题",
        "review.fixDesc": "Velie将自动创建修复PR",
        "review.reactionAsk": "这条审查有帮助吗？",
        "review.reactionThanks": "感谢你的反馈",
        "safety.critical": "危险",
        "safety.warning": "警告",
        "safety.clean": "安全",
        "onboarding.step1Title": "连接GitHub",
        "onboarding.step1Desc": "一键将Velie连接到你的仓库。30秒完成。",
        "onboarding.step1Detail": "Velie仅使用只读权限。不会修改你的代码。",
        "onboarding.step1Action": "安装GitHub App →",
        "onboarding.step2Title": "创建Pull Request",
        "onboarding.step2Desc": "像往常一样写代码并创建PR。无需特殊操作。",
        "onboarding.step2Detail": "Cursor、Copilot、v0、bolt.new — 任何工具都可以。",
        "onboarding.step3Title": "放心发布",
        "onboarding.step3Desc": "Velie AI自动检查。○△×安全评分一目了然。",
        "onboarding.step3Detail": "发现问题？点击「🔧 修复」按钮一键修复。",
        "onboarding.step3Action": "前往仪表盘 →",
        "onboarding.alreadyInstalled": "已安装 →",
        "onboarding.next": "完成，下一步 →",
        "onboarding.back": "← 返回",
        "onboarding.skip": "跳过前往仪表盘",
        "onboarding.stepOf": "步骤",
        "common.loading": "加载中...",
    },
};

// ---------------------------------------------------------------------------
// Translation function
// ---------------------------------------------------------------------------

export function t(key: keyof TranslationKeys, locale: Locale = DEFAULT_LOCALE, params?: Record<string, string | number>): string {
    let text = translations[locale]?.[key] || translations.ja[key] || key;

    if (params) {
        for (const [k, v] of Object.entries(params)) {
            text = text.replace(`{${k}}`, String(v));
        }
    }

    return text;
}

export function getTranslations(locale: Locale): TranslationKeys {
    return translations[locale] || translations.ja;
}
