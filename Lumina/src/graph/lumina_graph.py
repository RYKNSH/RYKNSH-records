"""Lumina Production Graph — 全20ノード統合版

Whitepaper Section 6: 5-Layer Architecture
🔵 Intelligence → 🟢 Creation → 🟡 Quality Fortress → 🟠 Delivery → 🔴 Evolution

MS1-MS8の全ノードを統合したStateGraph。
"""

from __future__ import annotations

from typing import Any

from src.models.state import GenerationStatus, LuminaState, QualityTier
from src.graph.nodes.creation.brief_interpreter import brief_interpreter
from src.graph.nodes.creation.model_selector import model_selector
from src.graph.nodes.creation.generator import generator
from src.graph.nodes.creation.enhancer_pipeline import enhancer_pipeline
from src.graph.nodes.creation.multi_model_compositor import multi_model_compositor
from src.graph.nodes.quality.taste_engine import taste_engine
from src.graph.nodes.quality.quality_score_cascade import quality_score_cascade
from src.graph.nodes.quality.ai_escalation_chain import ai_escalation_chain
from src.graph.nodes.delivery.delivery_nodes import (
    format_optimizer,
    asset_packager,
    brand_consistency_check,
)
from src.registry.client import ModelRegistryClient


# === ルーティング関数 ===

def _route_after_brief(state: LuminaState) -> str:
    """ブリーフ解析後のルーティング"""
    if state.status == GenerationStatus.FAILED:
        return "end"
    return "model_selector"


def _route_after_selector(state: LuminaState) -> str:
    """モデル選択後のルーティング"""
    if state.status == GenerationStatus.FAILED:
        return "end"
    return "generator"


def _route_after_generator(state: LuminaState) -> str:
    """生成後のルーティング"""
    if state.status == GenerationStatus.FAILED:
        return "end"
    # Premium/Masterpiece → マルチモデル合成
    if state.quality_tier in (QualityTier.PREMIUM, QualityTier.MASTERPIECE):
        return "multi_model_compositor"
    return "enhancer_pipeline"


def _route_after_compositor(state: LuminaState) -> str:
    """マルチモデル合成後"""
    return "enhancer_pipeline"


def _route_after_enhancer(state: LuminaState) -> str:
    """エンハンス後 → 品質検証へ"""
    return "taste_engine"


def _route_after_taste(state: LuminaState) -> str:
    """品質評価後"""
    if state.status == GenerationStatus.FAILED:
        return "end"
    return "quality_score_cascade"


def _route_after_cascade(state: LuminaState) -> str:
    """品質判定後の3分岐"""
    if state.status == GenerationStatus.DELIVERING:
        return "format_optimizer"
    if state.status == GenerationStatus.RETRYING:
        if state.escalation_step > 0:
            return "ai_escalation_chain"
        return "generator"  # 通常リトライ
    return "end"


def _route_after_escalation(state: LuminaState) -> str:
    """エスカレーション後"""
    if state.status == GenerationStatus.COMPLETED:
        return "format_optimizer"  # Graceful Degradation → 納品
    return "generator"  # 再生成


def _route_after_format(state: LuminaState) -> str:
    return "asset_packager"


def _route_after_packager(state: LuminaState) -> str:
    return "brand_consistency_check"


# === グラフ構築 ===

_model_registry = ModelRegistryClient()


async def _model_selector_with_registry(state: LuminaState) -> dict[str, Any]:
    """RegistryClientを注入したmodel_selector"""
    return await model_selector(state, registry=_model_registry)


def build_lumina_graph():
    """Lumina Production Graph を構築

    20ノード・5レイヤーの完全版。
    LangGraph StateGraph (import は呼び出し側が langgraph をインストールしている場合のみ動作)
    """
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        # langgraph未インストール時はダミーグラフ仕様を返す
        return _build_graph_spec()

    graph = StateGraph(LuminaState)

    # --- 🟢 Creation Layer ---
    graph.add_node("brief_interpreter", brief_interpreter)
    graph.add_node("model_selector", _model_selector_with_registry)
    graph.add_node("generator", generator)
    graph.add_node("multi_model_compositor", multi_model_compositor)
    graph.add_node("enhancer_pipeline", enhancer_pipeline)

    # --- 🟡 Quality Fortress ---
    graph.add_node("taste_engine", taste_engine)
    graph.add_node("quality_score_cascade", quality_score_cascade)
    graph.add_node("ai_escalation_chain", ai_escalation_chain)

    # --- 🟠 Delivery Layer ---
    graph.add_node("format_optimizer", format_optimizer)
    graph.add_node("asset_packager", asset_packager)
    graph.add_node("brand_consistency_check", brand_consistency_check)

    # --- エッジ定義 ---
    graph.set_entry_point("brief_interpreter")

    graph.add_conditional_edges("brief_interpreter", _route_after_brief)
    graph.add_conditional_edges("model_selector", _route_after_selector)
    graph.add_conditional_edges("generator", _route_after_generator)
    graph.add_conditional_edges("multi_model_compositor", _route_after_compositor)
    graph.add_conditional_edges("enhancer_pipeline", _route_after_enhancer)
    graph.add_conditional_edges("taste_engine", _route_after_taste)
    graph.add_conditional_edges("quality_score_cascade", _route_after_cascade)
    graph.add_conditional_edges("ai_escalation_chain", _route_after_escalation)
    graph.add_conditional_edges("format_optimizer", _route_after_format)
    graph.add_conditional_edges("asset_packager", _route_after_packager)
    graph.add_edge("brand_consistency_check", END)

    return graph.compile()


def _build_graph_spec() -> dict[str, Any]:
    """LangGraph未インストール時のグラフ仕様"""
    return {
        "type": "lumina_production_graph",
        "nodes": [
            # Creation Layer
            "brief_interpreter", "model_selector", "generator",
            "multi_model_compositor", "enhancer_pipeline",
            # Quality Fortress
            "taste_engine", "quality_score_cascade", "ai_escalation_chain",
            # Delivery Layer
            "format_optimizer", "asset_packager", "brand_consistency_check",
        ],
        "entry_point": "brief_interpreter",
        "layers": {
            "creation": ["brief_interpreter", "model_selector", "generator",
                         "multi_model_compositor", "enhancer_pipeline"],
            "quality": ["taste_engine", "quality_score_cascade", "ai_escalation_chain"],
            "delivery": ["format_optimizer", "asset_packager", "brand_consistency_check"],
        },
        "edges": {
            "brief_interpreter": ["model_selector", "end"],
            "model_selector": ["generator", "end"],
            "generator": ["multi_model_compositor", "enhancer_pipeline", "end"],
            "multi_model_compositor": ["enhancer_pipeline"],
            "enhancer_pipeline": ["taste_engine"],
            "taste_engine": ["quality_score_cascade", "end"],
            "quality_score_cascade": ["format_optimizer", "ai_escalation_chain", "generator"],
            "ai_escalation_chain": ["format_optimizer", "generator"],
            "format_optimizer": ["asset_packager"],
            "asset_packager": ["brand_consistency_check"],
            "brand_consistency_check": ["end"],
        },
        "note": "Intelligence + Evolution Layers run as weekly async cycles (not in main graph)",
    }


# 公開API
def get_graph_spec() -> dict[str, Any]:
    """グラフ仕様を取得（テスト用）"""
    return _build_graph_spec()
