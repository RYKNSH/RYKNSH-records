import { NextResponse } from "next/server";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

const SETTINGS_FILE = join(process.cwd(), "..", "data", "settings.json");

function loadSettings(): Record<string, unknown> {
    if (!existsSync(SETTINGS_FILE)) {
        return {
            llm_model: "claude-sonnet-4-20250514",
            review_language: "English",
            max_diff_size: "60,000 chars",
            email_on_critical: true,
            slack_integration: false,
        };
    }
    return JSON.parse(readFileSync(SETTINGS_FILE, "utf-8"));
}

function saveSettings(settings: Record<string, unknown>): void {
    const dir = join(process.cwd(), "..", "data");
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2));
}

export async function GET() {
    return NextResponse.json(loadSettings());
}

export async function POST(request: Request) {
    const body = await request.json();
    const current = loadSettings();
    const updated = { ...current, ...body };
    saveSettings(updated);
    return NextResponse.json({ success: true, settings: updated });
}
