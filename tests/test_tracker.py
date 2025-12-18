"""
Tests for the tracker module.
"""

import os
import tempfile
import pytest
from evoloop.tracker import monitor, log, get_storage, set_storage, set_context, clear_context
from evoloop.storage import SQLiteStorage
from evoloop.types import TraceContext


class TestMonitorDecorator:
    """Tests for the @monitor decorator."""

    @pytest.fixture(autouse=True)
    def setup_storage(self):
        """Use a temporary storage for each test."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        storage = SQLiteStorage(db_path=path)
        set_storage(storage)
        yield
        storage.close()
        os.unlink(path)

    def test_monitor_captures_input_output(self):
        @monitor
        def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        result = greet("World")
        assert result == "Hello, World!"
        
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 1
        assert traces[0].input == "World"
        assert traces[0].output == "Hello, World!"
        assert traces[0].status == "success"

    def test_monitor_with_kwargs(self):
        @monitor
        def process(a: int, b: int = 10) -> int:
            return a + b
        
        result = process(5, b=20)
        assert result == 25
        
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 1
        assert traces[0].input == {"args": [5], "kwargs": {"b": 20}}

    def test_monitor_captures_errors(self):
        @monitor
        def failing_function():
            raise ValueError("Something went wrong")
        
        with pytest.raises(ValueError):
            failing_function()
        
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 1
        assert traces[0].status == "error"
        assert "Something went wrong" in traces[0].error

    def test_monitor_with_name(self):
        @monitor(name="custom_agent")
        def my_agent(msg: str) -> str:
            return "response"
        
        my_agent("test")
        
        storage = get_storage()
        traces = storage.list_traces()
        assert traces[0].metadata["function_name"] == "custom_agent"

    def test_monitor_with_metadata(self):
        @monitor(metadata={"version": "1.0", "env": "test"})
        def my_agent(msg: str) -> str:
            return "response"
        
        my_agent("test")
        
        storage = get_storage()
        traces = storage.list_traces()
        assert traces[0].metadata["version"] == "1.0"
        assert traces[0].metadata["env"] == "test"

    def test_monitor_with_context(self):
        @monitor
        def agent_with_context(msg: str) -> str:
            return "response"
        
        # Context must be set BEFORE calling the function
        set_context(TraceContext(
            data={"api_balance": 1000},
            source="test_api"
        ))
        agent_with_context("test")
        
        storage = get_storage()
        traces = storage.list_traces()
        assert traces[0].context is not None
        assert traces[0].context.data["api_balance"] == 1000


class TestLogFunction:
    """Tests for the log() function."""

    @pytest.fixture(autouse=True)
    def setup_storage(self):
        """Use a temporary storage for each test."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        storage = SQLiteStorage(db_path=path)
        set_storage(storage)
        yield
        storage.close()
        os.unlink(path)

    def test_log_basic(self):
        trace = log(input_data="question", output_data="answer")
        
        assert trace.input == "question"
        assert trace.output == "answer"
        
        storage = get_storage()
        loaded = storage.load(trace.id)
        assert loaded is not None

    def test_log_with_all_params(self):
        ctx = TraceContext(data={"key": "value"})
        trace = log(
            input_data="in",
            output_data="out",
            context=ctx,
            metadata={"user": "123"},
            status="success",
            duration_ms=50.5,
        )
        
        assert trace.context.data["key"] == "value"
        assert trace.metadata["user"] == "123"
        assert trace.duration_ms == 50.5

    def test_log_error(self):
        trace = log(
            input_data="in",
            output_data=None,
            status="error",
            error="Failed to process",
        )
        
        assert trace.status == "error"
        assert trace.error == "Failed to process"
