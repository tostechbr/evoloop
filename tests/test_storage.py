"""
Tests for the storage module.
"""

import os
import tempfile
import pytest
from evoloop.storage import SQLiteStorage
from evoloop.types import Trace, TraceContext


class TestSQLiteStorage:
    """Tests for SQLiteStorage."""

    @pytest.fixture
    def storage(self):
        """Create a temporary storage for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        storage = SQLiteStorage(db_path=path)
        yield storage
        storage.close()
        os.unlink(path)

    def test_save_and_load(self, storage):
        trace = Trace(input="hello", output="world")
        storage.save(trace)
        
        loaded = storage.load(trace.id)
        assert loaded is not None
        assert loaded.id == trace.id
        assert loaded.input == "hello"
        assert loaded.output == "world"

    def test_save_with_context(self, storage):
        ctx = TraceContext(data={"balance": 1000}, source="api")
        trace = Trace(input="test", output="result", context=ctx)
        storage.save(trace)
        
        loaded = storage.load(trace.id)
        assert loaded.context is not None
        assert loaded.context.data["balance"] == 1000
        assert loaded.context.source == "api"

    def test_save_with_metadata(self, storage):
        trace = Trace(
            input="test",
            output="result",
            metadata={"user_id": "123", "session": "abc"}
        )
        storage.save(trace)
        
        loaded = storage.load(trace.id)
        assert loaded.metadata["user_id"] == "123"
        assert loaded.metadata["session"] == "abc"

    def test_load_nonexistent(self, storage):
        loaded = storage.load("nonexistent-id")
        assert loaded is None

    def test_list_traces(self, storage):
        for i in range(5):
            trace = Trace(input=f"input-{i}", output=f"output-{i}")
            storage.save(trace)
        
        traces = storage.list_traces(limit=3)
        assert len(traces) == 3

    def test_list_traces_with_status_filter(self, storage):
        storage.save(Trace(input="ok", output="ok", status="success"))
        storage.save(Trace(input="err", output=None, status="error", error="failed"))
        storage.save(Trace(input="ok2", output="ok2", status="success"))
        
        success_traces = storage.list_traces(status="success")
        error_traces = storage.list_traces(status="error")
        
        assert len(success_traces) == 2
        assert len(error_traces) == 1

    def test_count(self, storage):
        assert storage.count() == 0
        
        storage.save(Trace(input="1", output="1"))
        storage.save(Trace(input="2", output="2"))
        storage.save(Trace(input="3", output=None, status="error"))
        
        assert storage.count() == 3
        assert storage.count(status="success") == 2
        assert storage.count(status="error") == 1

    def test_iter_traces(self, storage):
        for i in range(3):
            storage.save(Trace(input=f"in-{i}", output=f"out-{i}"))
        
        traces = list(storage.iter_traces())
        assert len(traces) == 3

    def test_clear(self, storage):
        storage.save(Trace(input="1", output="1"))
        storage.save(Trace(input="2", output="2"))
        assert storage.count() == 2
        
        storage.clear()
        assert storage.count() == 0

    def test_complex_input_output(self, storage):
        """Test with complex nested data structures."""
        trace = Trace(
            input={"messages": [{"role": "user", "content": "hello"}]},
            output={"messages": [{"role": "assistant", "content": "hi"}]},
        )
        storage.save(trace)
        
        loaded = storage.load(trace.id)
        assert loaded.input["messages"][0]["content"] == "hello"
        assert loaded.output["messages"][0]["content"] == "hi"
