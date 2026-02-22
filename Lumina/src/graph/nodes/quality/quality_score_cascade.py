"""quality_score_cascade — 品質スコア比較ノード

Whitepaper Section 6 > Quality Fortress > quality_score_cascade:
Taste Engineスコアをテナント要求水準と比較。
未達→Auto-Retry。リトライ上限→AI Escalation Chain。
"""

from __future__ import annotations

from typing import Any

from src.models.state import GenerationStatus, LuminaState


async def quality_score_cascade(state: LuminaState) -> dict[str, Any]:
    """品質スコアとテナント要求水準を比較する

    - 合格: → DELIVERING（納品へ）
    - 不合格 & リトライ可能: → RETRYING（リトライ）
    - 不合格 & リトライ上限: → ai_escalation_chain へ
    """
    if state.taste_score is None:
        return {
            "status": GenerationStatus.FAILED,
            "error": "Taste Engine未実行",
        }

    score = state.taste_score.aggregated
    threshold = state.quality_threshold

    # Preview ティアは無条件通過
    if state.quality_tier.value == "preview":
        return {"status": GenerationStatus.DELIVERING}

    # 品質基準を満たしている
    if score >= threshold:
        return {"status": GenerationStatus.DELIVERING}

    # 品質基準未達 — リトライ可能か
    if state.can_retry():
        return {
            "retry_count": state.retry_count + 1,
            "status": GenerationStatus.RETRYING,
        }

    # リトライ上限到達 → AI Escalation Chain
    return {
        "status": GenerationStatus.RETRYING,
        "escalation_step": 1,
    }
