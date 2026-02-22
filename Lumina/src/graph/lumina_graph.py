"""Lumina Graph — LangGraph メイングラフ定義

5-Layer Architecture の Creation Layer (MS1) を
LangGraph StateGraph で定義。

Whitepaper Section 5:
  🟢 CREATION: brief_interpreter → model_selector → generator
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from src.graph.nodes.creation.brief_interpreter import brief_interpreter
from src.graph.nodes.creation.generator import generator
from src.graph.nodes.creation.model_selector import model_selector
from src.models.state import GenerationStatus, LuminaState
from src.registry.client import ModelRegistryClient


def _should_continue_after_selector(state: dict[str, Any]) -> str:
    """model_selector の後のルーティング"""
    if state.get("status") == GenerationStatus.FAILED:
        return END
    return "generator"


def _should_continue_after_generator(state: dict[str, Any]) -> str:
    """generator の後のルーティング（MS1: 直接終了）

    MS2以降: Quality Fortress (taste_engine) に進む
    """
    return END


def build_lumina_graph(
    registry: ModelRegistryClient | None = None,
) -> StateGraph:
    """Lumina の LangGraph グラフを構築

    MS1: Creation Layer のみ
      brief_interpreter → model_selector → generator → END

    MS2以降に拡張:
      → taste_engine → quality_score_cascade → [deliver | retry]
    """
    if registry is None:
        registry = ModelRegistryClient()

    # model_selector にレジストリを注入するラッパー
    async def _model_selector_with_registry(state: LuminaState) -> dict[str, Any]:
        return await model_selector(state, registry=registry)

    graph = StateGraph(LuminaState)

    # ノード追加
    graph.add_node("brief_interpreter", brief_interpreter)
    graph.add_node("model_selector", _model_selector_with_registry)
    graph.add_node("generator", generator)

    # エッジ: エントリ → brief_interpreter
    graph.set_entry_point("brief_interpreter")

    # エッジ: brief_interpreter → model_selector（失敗時はEND）
    graph.add_conditional_edges(
        "brief_interpreter",
        lambda state: END if state.get("status") == GenerationStatus.FAILED else "model_selector",
    )

    # エッジ: model_selector → generator（失敗時はEND）
    graph.add_conditional_edges(
        "model_selector",
        _should_continue_after_selector,
    )

    # エッジ: generator → END
    graph.add_conditional_edges(
        "generator",
        _should_continue_after_generator,
    )

    return graph


def compile_lumina_graph(
    registry: ModelRegistryClient | None = None,
) -> Any:
    """コンパイル済みグラフを返す"""
    graph = build_lumina_graph(registry)
    return graph.compile()
