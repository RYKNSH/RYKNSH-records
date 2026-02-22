"""Model Registry クライアントのテスト"""

import pytest

from src.registry.client import ModelRegistryClient, RegisteredModel


@pytest.mark.asyncio
async def test_registry_seed_data():
    """seedデータが正しくロードされる"""
    client = ModelRegistryClient()
    models = await client.get_active_models()

    assert len(models) == 3
    assert any(m.id == "flux-1.1-pro" for m in models)
    assert any(m.id == "dall-e-3" for m in models)
    assert any(m.id == "sd-xl-turbo" for m in models)


@pytest.mark.asyncio
async def test_registry_get_model():
    """特定モデルの取得"""
    client = ModelRegistryClient()
    model = await client.get_model("flux-1.1-pro")

    assert model is not None
    assert model.model_name == "Flux 1.1 Pro"
    assert model.provider == "black-forest-labs"


@pytest.mark.asyncio
async def test_registry_get_best_model():
    """最適モデル選択"""
    client = ModelRegistryClient()
    best = await client.get_best_model(model_type="image")

    assert best is not None
    assert best.capability_score >= 85  # Flux or DALL-E


@pytest.mark.asyncio
async def test_registry_get_best_model_with_cost_limit():
    """コスト制限付きモデル選択"""
    client = ModelRegistryClient()
    best = await client.get_best_model(model_type="image", max_cost=0.02)

    assert best is not None
    assert best.cost_per_call <= 0.02
    assert best.id == "sd-xl-turbo"


@pytest.mark.asyncio
async def test_registry_task_style_selection():
    """タスクスタイルに応じた選択"""
    client = ModelRegistryClient()

    text_model = await client.get_best_model(task_style="text_heavy")
    assert text_model is not None
    assert text_model.id == "dall-e-3"  # text_rendering最高

    artistic_model = await client.get_best_model(task_style="artistic")
    assert artistic_model is not None
    assert artistic_model.id == "sd-xl-turbo"  # artistic最高


@pytest.mark.asyncio
async def test_registry_register_and_deactivate():
    """モデル登録と無効化"""
    client = ModelRegistryClient()

    new_model = RegisteredModel(
        id="test-model",
        model_name="Test Model",
        model_type="image",
        provider="test",
        capability_score=99,
        cost_per_call=0.01,
    )

    await client.register_model(new_model)
    fetched = await client.get_model("test-model")
    assert fetched is not None
    assert fetched.is_active is True

    await client.deactivate_model("test-model")
    fetched = await client.get_model("test-model")
    assert fetched is not None
    assert fetched.is_active is False
