import pytest
from unittest.mock import MagicMock
from evoloop import wrap, get_storage
from evoloop.types import Trace

class MockLangGraphAgent:
    """Simulates a LangGraph agent with invoke and stream methods."""
    def invoke(self, input_data):
        return {"messages": [{"content": "Mock response"}]}

    def stream(self, input_data):
        yield {"messages": ["chunk1"]}
        yield {"messages": ["chunk2"]}

def test_wrap_langgraph_invoke():
    """Test that wrap() correctly handles invoke() calls."""
    agent = MockLangGraphAgent()
    monitored_agent = wrap(agent, name="mock_agent")
    
    # Run invoke
    result = monitored_agent.invoke({"input": "test"})
    
    # Verify result is passed through
    assert result == {"messages": [{"content": "Mock response"}]}
    
    # Verify trace was created
    storage = get_storage()
    traces = storage.list_traces(limit=1)
    assert len(traces) == 1
    assert traces[0].metadata["method"] == "invoke"
    assert traces[0].input == {"input": "test"}
    assert traces[0].output == {"messages": [{"content": "Mock response"}]}

def test_wrap_langgraph_stream():
    """Test that wrap() correctly handles stream() calls."""
    agent = MockLangGraphAgent()
    monitored_agent = wrap(agent, name="mock_agent_stream")
    
    # Run stream
    chunks = list(monitored_agent.stream({"input": "stream_test"}))
    
    # Verify chunks are passed through
    assert chunks == [{"messages": ["chunk1"]}, {"messages": ["chunk2"]}]
    
    # Verify trace was created
    storage = get_storage()
    # We might have multiple traces from previous tests, so filter or get latest
    traces = storage.list_traces(limit=1)
    assert len(traces) > 0
    # The most recent trace should be the stream one
    trace = traces[0]
    
    assert trace.metadata["method"] == "stream"
    assert trace.input == {"input": "stream_test"}
    # Stream output is captured as a list of chunks
    assert trace.output == {"messages": ["chunk1", "chunk2"]}
