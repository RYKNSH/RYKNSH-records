"""Tests for agent.tools — Tool SDK base classes."""

import pytest

from pydantic import BaseModel

from agent.tools.base import AdaTool, ToolRegistry, get_global_registry


# --- Test Fixtures ---


class MockInputSchema(BaseModel):
    query: str
    limit: int = 10


class MockTool(AdaTool):
    """A mock tool for testing."""

    name = "mock_search"
    description = "Search for something"

    def get_input_schema(self) -> type[BaseModel]:
        return MockInputSchema

    async def execute(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 10)
        return f"Found {limit} results for '{query}'"


class AnotherMockTool(AdaTool):
    """Another mock tool."""

    name = "mock_calculator"
    description = "Calculate something"

    def get_input_schema(self) -> type[BaseModel]:
        class CalcInput(BaseModel):
            expression: str

        return CalcInput

    async def execute(self, **kwargs) -> str:
        return f"Result: {kwargs.get('expression', '0')}"


class EmptyNameTool(AdaTool):
    """Tool with empty name (should fail registration)."""

    name = ""
    description = "Invalid tool"

    def get_input_schema(self) -> type[BaseModel]:
        return BaseModel

    async def execute(self, **kwargs) -> str:
        return ""


# --- ToolRegistry Tests ---


class TestToolRegistry:
    """Test ToolRegistry registration and retrieval."""

    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        assert registry.get("mock_search") is tool

    def test_get_nonexistent_returns_none(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())
        names = registry.list_tools()
        assert "mock_search" in names
        assert "mock_calculator" in names
        assert len(names) == 2

    def test_len(self):
        registry = ToolRegistry()
        assert len(registry) == 0
        registry.register(MockTool())
        assert len(registry) == 1

    def test_contains(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        assert "mock_search" in registry
        assert "nonexistent" not in registry

    def test_clear(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())
        assert len(registry) == 2
        registry.clear()
        assert len(registry) == 0

    def test_register_overwrites(self):
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = MockTool()
        registry.register(tool1)
        registry.register(tool2)
        assert registry.get("mock_search") is tool2
        assert len(registry) == 1

    def test_register_empty_name_raises(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="non-empty name"):
            registry.register(EmptyNameTool())

    def test_to_langchain_tools(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())
        lc_tools = registry.to_langchain_tools()
        assert len(lc_tools) == 2
        names = {t.name for t in lc_tools}
        assert names == {"mock_search", "mock_calculator"}


# --- AdaTool Tests ---


class TestAdaTool:
    """Test AdaTool interface and LangChain conversion."""

    def test_to_langchain_tool(self):
        tool = MockTool()
        lc_tool = tool.to_langchain_tool()
        assert lc_tool.name == "mock_search"
        assert lc_tool.description == "Search for something"

    @pytest.mark.asyncio
    async def test_execute(self):
        tool = MockTool()
        result = await tool.execute(query="hello", limit=5)
        assert result == "Found 5 results for 'hello'"

    @pytest.mark.asyncio
    async def test_langchain_tool_invoke(self):
        tool = MockTool()
        lc_tool = tool.to_langchain_tool()
        result = await lc_tool.ainvoke({"query": "test", "limit": 3})
        assert result == "Found 3 results for 'test'"

    def test_input_schema(self):
        tool = MockTool()
        schema = tool.get_input_schema()
        assert schema.__name__ == "MockInputSchema"
        fields = schema.model_fields
        assert "query" in fields
        assert "limit" in fields


# --- Global Registry Tests ---


class TestGlobalRegistry:
    """Test the global registry singleton."""

    def test_singleton(self):
        r1 = get_global_registry()
        r2 = get_global_registry()
        assert r1 is r2

    def test_global_registry_is_tool_registry(self):
        registry = get_global_registry()
        assert isinstance(registry, ToolRegistry)
