"""
Tests for the types module.
"""

import pytest
from evoloop.types import Trace, TraceContext


class TestTraceContext:
    """Tests for TraceContext dataclass."""

    def test_create_empty_context(self):
        ctx = TraceContext()
        assert ctx.data == {}
        assert ctx.source is None

    def test_create_context_with_data(self):
        ctx = TraceContext(
            data={"api_response": {"balance": 1000}},
            source="customer_api"
        )
        assert ctx.data["api_response"]["balance"] == 1000
        assert ctx.source == "customer_api"

    def test_to_dict(self):
        ctx = TraceContext(data={"key": "value"}, source="test")
        d = ctx.to_dict()
        assert d == {"data": {"key": "value"}, "source": "test"}

    def test_from_dict(self):
        d = {"data": {"key": "value"}, "source": "test"}
        ctx = TraceContext.from_dict(d)
        assert ctx.data == {"key": "value"}
        assert ctx.source == "test"


class TestTrace:
    """Tests for Trace dataclass."""

    def test_create_simple_trace(self):
        trace = Trace(input="hello", output="world")
        assert trace.input == "hello"
        assert trace.output == "world"
        assert trace.status == "success"
        assert trace.id is not None
        assert trace.timestamp is not None

    def test_create_trace_with_all_fields(self):
        ctx = TraceContext(data={"test": True})
        trace = Trace(
            input="input",
            output="output",
            context=ctx,
            duration_ms=100.5,
            status="error",
            error="Something went wrong",
            metadata={"user_id": "123"},
        )
        assert trace.context.data["test"] is True
        assert trace.duration_ms == 100.5
        assert trace.status == "error"
        assert trace.error == "Something went wrong"
        assert trace.metadata["user_id"] == "123"

    def test_to_dict(self):
        trace = Trace(input="in", output="out")
        d = trace.to_dict()
        assert d["input"] == "in"
        assert d["output"] == "out"
        assert "id" in d
        assert "timestamp" in d

    def test_from_dict(self):
        d = {
            "id": "test-id",
            "input": "in",
            "output": "out",
            "timestamp": "2025-01-01T00:00:00",
            "status": "success",
        }
        trace = Trace.from_dict(d)
        assert trace.id == "test-id"
        assert trace.input == "in"
        assert trace.output == "out"

    def test_serialize_dict(self):
        trace = Trace(input={"key": "value"}, output={"result": 42})
        d = trace.to_dict()
        assert d["input"] == {"key": "value"}
        assert d["output"] == {"result": 42}

    def test_serialize_list(self):
        trace = Trace(input=[1, 2, 3], output=["a", "b", "c"])
        d = trace.to_dict()
        assert d["input"] == [1, 2, 3]
        assert d["output"] == ["a", "b", "c"]
