"""
Simple Q&A Agent Example

This example demonstrates how to use EvoLoop to monitor a simple Q&A agent.
It shows all three monitoring methods:
1. @monitor decorator
2. wrap() for LangGraph-style agents  
3. log() for manual control
"""

from evoloop import monitor, log, get_storage, TraceContext


# =============================================================================
# Example 1: Using the @monitor decorator (Simplest approach)
# =============================================================================

@monitor
def simple_qa_agent(question: str) -> str:
    """
    A simple Q&A agent that answers questions.
    
    In a real scenario, this would call an LLM API.
    The @monitor decorator automatically captures the input/output.
    """
    # Simulate agent logic
    if "capital" in question.lower():
        return "Paris is the capital of France."
    elif "weather" in question.lower():
        return "I don't have access to real-time weather data."
    else:
        return "I'm not sure how to answer that question."


# =============================================================================
# Example 2: Using @monitor with context (Business rules scenario)
# =============================================================================

from evoloop.tracker import set_context

@monitor(name="debt_negotiation_agent", metadata={"version": "1.0"})
def debt_agent(user_message: str, customer_data: dict) -> str:
    """
    An agent that negotiates debt payments.
    
    This example shows how to attach context (API data) to the trace
    for later evaluation against business rules.
    """
    # Attach the customer data as context for evaluation
    set_context(TraceContext(
        data=customer_data,
        source="customer_api"
    ))
    
    debt_amount = customer_data.get("debt_amount", 0)
    max_discount = customer_data.get("max_discount_percent", 0)
    
    # Simulate agent response (in reality, this would be an LLM)
    if "discount" in user_message.lower():
        # BUG: Agent offers 50% but max allowed is 30%
        # This should be caught by the EvoLoop Judge later
        return f"I can offer you a 50% discount on your debt of ${debt_amount}!"
    
    return f"Your current debt is ${debt_amount}. How can I help you today?"


# =============================================================================
# Example 3: Using log() for manual control
# =============================================================================

def custom_agent_flow():
    """
    Example using manual logging for complex flows.
    """
    import time
    
    user_input = "What's 2 + 2?"
    start_time = time.perf_counter()
    
    # Your complex agent logic here
    result = "2 + 2 = 4"
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Manually log the trace
    trace = log(
        input_data=user_input,
        output_data=result,
        metadata={"source": "custom_flow", "user_id": "user_123"},
        duration_ms=duration_ms,
    )
    
    return result, trace.id


# =============================================================================
# Run examples
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EvoLoop - Simple Q&A Agent Example")
    print("=" * 60)
    
    # Example 1: Simple decorator
    print("\n[Example 1] Using @monitor decorator:")
    response1 = simple_qa_agent("What is the capital of France?")
    print(f"  Q: What is the capital of France?")
    print(f"  A: {response1}")
    
    response2 = simple_qa_agent("What's the weather like?")
    print(f"  Q: What's the weather like?")
    print(f"  A: {response2}")
    
    # Example 2: With context
    print("\n[Example 2] Using @monitor with context:")
    customer = {
        "debt_amount": 1500,
        "max_discount_percent": 30,
        "customer_id": "C12345"
    }
    response3 = debt_agent("Can I get a discount?", customer)
    print(f"  Customer debt: ${customer['debt_amount']}")
    print(f"  Max discount allowed: {customer['max_discount_percent']}%")
    print(f"  Agent response: {response3}")
    print("  ⚠️  Note: Agent offered 50% but max is 30% - this should fail evaluation!")
    
    # Example 3: Manual logging
    print("\n[Example 3] Using manual log():")
    result, trace_id = custom_agent_flow()
    print(f"  Result: {result}")
    print(f"  Trace ID: {trace_id}")
    
    # Show stored traces
    print("\n" + "=" * 60)
    print("Stored Traces Summary")
    print("=" * 60)
    
    storage = get_storage()
    traces = storage.list_traces(limit=10)
    
    print(f"\nTotal traces captured: {storage.count()}")
    print(f"Successful: {storage.count(status='success')}")
    print(f"Errors: {storage.count(status='error')}")
    
    print("\nRecent traces:")
    for i, trace in enumerate(traces, 1):
        print(f"  {i}. [{trace.status.upper()}] {trace.metadata.get('function_name', 'N/A')}")
        print(f"     Input: {str(trace.input)[:50]}...")
        print(f"     Duration: {trace.duration_ms:.2f}ms")
    
    print("\n✅ All traces saved to 'evoloop.db'")
    print("   Run 'evoloop eval' to evaluate traces (coming in Phase 2)")
