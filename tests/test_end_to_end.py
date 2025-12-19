"""
End-to-end integration tests for EvoLoop.

Tests the complete workflow of monitoring agents, storing traces,
and retrieving them for analysis.
"""

import os
import tempfile
import pytest
from evoloop import monitor, wrap, log, get_storage
from evoloop.storage import SQLiteStorage
from evoloop.tracker import set_storage, set_context
from evoloop.types import TraceContext


class TestEndToEndWorkflow:
    """Test complete EvoLoop workflows."""

    @pytest.fixture(autouse=True)
    def setup_storage(self):
        """Use a temporary storage for each test."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        storage = SQLiteStorage(db_path=path)
        set_storage(storage)
        yield storage
        storage.close()
        os.unlink(path)

    def test_complete_workflow_with_decorator(self, setup_storage):
        """Test complete workflow using @monitor decorator."""
        # Define a monitored agent
        @monitor(name="test_agent", metadata={"version": "1.0"})
        def my_agent(question: str) -> str:
            if "hello" in question.lower():
                return "Hi there!"
            return "I don't understand."

        # Run the agent multiple times
        response1 = my_agent("Hello world")
        response2 = my_agent("What is AI?")

        assert response1 == "Hi there!"
        assert response2 == "I don't understand."

        # Verify traces were captured
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 2

        # Verify trace content
        assert traces[0].input == "What is AI?"
        assert traces[0].output == "I don't understand."
        assert traces[0].status == "success"
        assert traces[0].metadata["function_name"] == "test_agent"
        assert traces[0].metadata["version"] == "1.0"

        assert traces[1].input == "Hello world"
        assert traces[1].output == "Hi there!"

    def test_complete_workflow_with_context(self, setup_storage):
        """Test workflow with context data for business rules."""
        @monitor(name="pricing_agent")
        def pricing_agent(query: str, customer_data: dict) -> str:
            max_discount = customer_data.get("max_discount", 10)
            return f"I can offer you a {max_discount}% discount."

        customer = {"customer_id": "C123", "max_discount": 20}

        # Attach customer context before calling the function
        set_context(TraceContext(
            data=customer,
            source="customer_api"
        ))

        response = pricing_agent("Can I get a discount?", customer)

        assert "20%" in response

        # Verify trace with context
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 1
        assert traces[0].context is not None
        assert traces[0].context.data["customer_id"] == "C123"
        assert traces[0].context.source == "customer_api"

    def test_complete_workflow_with_manual_logging(self, setup_storage):
        """Test workflow using manual logging."""
        # Simulate an agent execution
        user_input = "Calculate 2 + 2"
        agent_output = "The answer is 4"

        # Manually log the trace
        trace = log(
            input_data=user_input,
            output_data=agent_output,
            metadata={"source": "calculator", "user_id": "user123"},
            duration_ms=15.5,
        )

        # Verify trace was saved
        storage = get_storage()
        loaded_trace = storage.load(trace.id)

        assert loaded_trace is not None
        assert loaded_trace.input == user_input
        assert loaded_trace.output == agent_output
        assert loaded_trace.metadata["source"] == "calculator"
        assert loaded_trace.duration_ms == 15.5

    def test_error_handling_workflow(self, setup_storage):
        """Test that errors are properly captured."""
        @monitor
        def failing_agent(msg: str) -> str:
            if "error" in msg.lower():
                raise ValueError("Intentional error for testing")
            return "Success"

        # Normal execution
        result = failing_agent("normal message")
        assert result == "Success"

        # Error execution
        with pytest.raises(ValueError):
            failing_agent("trigger error")

        # Verify both traces
        storage = get_storage()
        all_traces = storage.list_traces()
        assert len(all_traces) == 2

        success_traces = storage.list_traces(status="success")
        error_traces = storage.list_traces(status="error")

        assert len(success_traces) == 1
        assert len(error_traces) == 1
        assert "Intentional error" in error_traces[0].error

    def test_storage_operations(self, setup_storage):
        """Test various storage operations."""
        storage = get_storage()

        # Create multiple traces
        for i in range(10):
            status = "error" if i % 3 == 0 else "success"
            log(
                input_data=f"input-{i}",
                output_data=f"output-{i}",
                status=status,
                error=f"error-{i}" if status == "error" else None,
                metadata={"index": i},
            )

        # Test count operations
        assert storage.count() == 10
        assert storage.count(status="success") == 6
        assert storage.count(status="error") == 4

        # Test pagination
        page1 = storage.list_traces(limit=5, offset=0)
        page2 = storage.list_traces(limit=5, offset=5)
        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0].id != page2[0].id

        # Test iteration
        all_traces = list(storage.iter_traces())
        assert len(all_traces) == 10

    def test_scalability_stress_test(self, setup_storage):
        """Test system with larger volume of traces."""
        storage = get_storage()

        # Create a significant number of traces
        num_traces = 100

        for i in range(num_traces):
            log(
                input_data={"question": f"Query {i}", "context": {"index": i}},
                output_data={"answer": f"Response {i}", "confidence": 0.95},
                metadata={"batch": "stress_test", "index": i},
                duration_ms=float(i % 50),
            )

        # Verify all traces were stored
        assert storage.count() == num_traces

        # Verify retrieval performance
        recent_traces = storage.list_traces(limit=10)
        assert len(recent_traces) == 10

        # Verify filtering works at scale
        first_trace = storage.list_traces(limit=1, offset=0)
        last_trace = storage.list_traces(limit=1, offset=num_traces - 1)
        assert first_trace[0].id != last_trace[0].id


class MockLangGraphAgent:
    """Mock agent simulating LangGraph interface."""

    def __init__(self, name: str = "mock_agent"):
        self.name = name

    def invoke(self, input_data: dict) -> dict:
        """Simulate LangGraph invoke."""
        messages = input_data.get("messages", [])
        return {
            "messages": messages + [{"role": "assistant", "content": "Mock response"}]
        }

    def stream(self, input_data: dict):
        """Simulate LangGraph stream."""
        yield {"agent": {"messages": [{"role": "assistant", "content": "Part 1"}]}}
        yield {"agent": {"messages": [{"role": "assistant", "content": "Part 2"}]}}


class TestWrapperIntegration:
    """Test agent wrapper integration."""

    @pytest.fixture(autouse=True)
    def setup_storage(self):
        """Use a temporary storage for each test."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        storage = SQLiteStorage(db_path=path)
        set_storage(storage)
        yield storage
        storage.close()
        os.unlink(path)

    def test_wrapper_with_mock_agent(self, setup_storage):
        """Test wrapper with mock LangGraph-style agent."""
        agent = MockLangGraphAgent("test_agent")
        monitored_agent = wrap(agent, name="monitored_test_agent")

        # Test invoke
        result = monitored_agent.invoke({
            "messages": [{"role": "user", "content": "Hello"}]
        })

        assert len(result["messages"]) == 2
        assert result["messages"][-1]["content"] == "Mock response"

        # Verify trace was captured
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 1
        assert traces[0].metadata["agent_name"] == "monitored_test_agent"
        assert traces[0].metadata["method"] == "invoke"

    def test_wrapper_stream_integration(self, setup_storage):
        """Test wrapper with streaming."""
        agent = MockLangGraphAgent("streaming_agent")
        monitored_agent = wrap(agent)

        chunks = list(monitored_agent.stream({
            "messages": [{"role": "user", "content": "Stream test"}]
        }))

        assert len(chunks) == 2
        assert chunks[0]["agent"]["messages"][0]["content"] == "Part 1"

        # Verify trace was captured with streaming method
        storage = get_storage()
        traces = storage.list_traces()
        assert len(traces) == 1
        assert traces[0].metadata["method"] == "stream"
