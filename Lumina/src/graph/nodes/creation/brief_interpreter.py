"""brief_interpreter — ブリーフ解析ノード

クライアントの自然言語ブリーフを構造化パラメータ（BriefParams）に変換する。
Creation Layer の最初のノード。

Whitepaper Section 6 > Creation Layer > brief_interpreter:
「クライアントブリーフの深層解析。曖昧な指示を構造化された生成パラメータに変換。
 参照セット（pgvector）から類似成功作品を検索してコンテキスト注入」
"""

from __future__ import annotations

import json
from typing import Any

from src.models.state import BriefParams, GenerationStatus, LuminaState


BRIEF_INTERPRETATION_PROMPT = """あなたはLuminaのブリーフ解析AIです。
クライアントの自然言語ブリーフを構造化パラメータに変換してください。

## ブリーフ
{brief}

## 品質ティア
{quality_tier}

## アセット種別
{asset_type}

## 出力形式
以下のJSON形式で返してください:
```json
{{
  "subject": "メインの被写体/主題",
  "style": "ビジュアルスタイル（例: cyberpunk, minimalist, watercolor）",
  "mood": "雰囲気・トーン（例: dark, vibrant, dreamy）",
  "color_palette": ["主要カラー1", "主要カラー2"],
  "composition_hints": ["構図の指示1", "構図の指示2"],
  "negative_prompts": ["避けるべき要素1"],
  "prompt": "生成モデルに渡す最終プロンプト（英語）"
}}
```
"""


async def brief_interpreter(state: LuminaState) -> dict[str, Any]:
    """ブリーフを構造化パラメータに変換する

    LLM（Ada API）を使用してブリーフを解析し、
    生成モデルに渡すパラメータを生成する。

    開発時: ブリーフからの直接変換（LLMなし）
    本番時: Ada Core API を使用した深層解析
    """
    if not state.brief:
        return {
            "status": GenerationStatus.FAILED,
            "error": "ブリーフが空です",
        }

    # フェーズ1: ルールベースの直接変換（LLM不要）
    # 本番時にはAda Core APIによる深層解析に置き換え
    brief_params = _rule_based_interpretation(state.brief, state.asset_type.value)

    return {
        "brief_params": brief_params,
        "status": GenerationStatus.SELECTING,
    }


def _rule_based_interpretation(brief: str, asset_type: str) -> BriefParams:
    """ルールベースのブリーフ解析（MVP用）

    LLMなしでも動作するフォールバック実装。
    本番ではAda APIによる深層解析が優先される。
    """
    brief_lower = brief.lower()

    # スタイル推定
    style_keywords = {
        "cyberpunk": "cyberpunk",
        "サイバーパンク": "cyberpunk",
        "minimalist": "minimalist",
        "ミニマル": "minimalist",
        "watercolor": "watercolor",
        "水彩": "watercolor",
        "retro": "retro",
        "レトロ": "retro",
        "anime": "anime",
        "アニメ": "anime",
        "photorealistic": "photorealistic",
        "写実": "photorealistic",
    }

    detected_style = "general"
    for keyword, style in style_keywords.items():
        if keyword in brief_lower:
            detected_style = style
            break

    # ムード推定
    mood_keywords = {
        "dark": "dark",
        "暗い": "dark",
        "ダーク": "dark",
        "vibrant": "vibrant",
        "鮮やか": "vibrant",
        "dreamy": "dreamy",
        "幻想的": "dreamy",
        "calm": "calm",
        "落ち着いた": "calm",
        "energetic": "energetic",
        "エネルギッシュ": "energetic",
    }

    detected_mood = "neutral"
    for keyword, mood in mood_keywords.items():
        if keyword in brief_lower:
            detected_mood = mood
            break

    return BriefParams(
        subject=brief[:100],
        style=detected_style,
        mood=detected_mood,
        prompt=f"{brief}. Style: {detected_style}. Mood: {detected_mood}.",
    )
