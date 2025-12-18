"""
LangGraph Integration Example

This example shows how to use EvoLoop with LangGraph agents.
The wrap() function provides seamless integration with LangGraph's
.invoke() and .stream() methods.

NOTE: This example requires langgraph to be installed:
    pip install langgraph langchain-openai
"""

# Uncomment and run when you have LangGraph installed

"""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from evoloop import wrap, get_storage
from evoloop.tracker import set_context
from evoloop.types import TraceContext


# Create a simple tool
def get_weather(city: str) -> str:
    '''Get the weather for a city.'''
    return f"The weather in {city} is sunny, 25°C"


def get_stock_price(symbol: str) -> str:
    '''Get the stock price for a symbol.'''
    return f"The stock price of {symbol} is $150.00"


# Create the LangGraph agent
model = ChatOpenAI(model="gpt-4o-mini")
tools = [get_weather, get_stock_price]

agent = create_react_agent(model, tools)

# Wrap the agent with EvoLoop monitoring
monitored_agent = wrap(agent, name="weather_stock_agent")


# Use the agent as normal - traces are captured automatically
def main():
    print("=" * 60)
    print("EvoLoop + LangGraph Integration Example")
    print("=" * 60)
    
    # Example 1: Simple invoke
    print("\n[Example 1] Weather query:")
    result = monitored_agent.invoke({
        "messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]
    })
    print(f"Agent response: {result['messages'][-1].content}")
    
    # Example 2: With context (e.g., user preferences from database)
    print("\n[Example 2] Stock query with user context:")
    set_context(TraceContext(
        data={"user_tier": "premium", "allowed_symbols": ["AAPL", "GOOGL", "MSFT"]},
        source="user_database"
    ))
    result = monitored_agent.invoke({
        "messages": [{"role": "user", "content": "What's Apple's stock price?"}]
    })
    print(f"Agent response: {result['messages'][-1].content}")
    
    # Example 3: Streaming
    print("\n[Example 3] Streaming response:")
    for chunk in monitored_agent.stream({
        "messages": [{"role": "user", "content": "Weather in Paris and GOOGL stock?"}]
    }):
        if "agent" in chunk:
            print(f"  Agent: {chunk['agent']}")
    
    # Show captured traces
    print("\n" + "=" * 60)
    print("Captured Traces")
    print("=" * 60)
    
    storage = get_storage()
    traces = storage.list_traces(limit=5)
    
    for trace in traces:
        print(f"\nTrace ID: {trace.id[:8]}...")
        print(f"  Method: {trace.metadata.get('method', 'N/A')}")
        print(f"  Duration: {trace.duration_ms:.2f}ms")
        print(f"  Status: {trace.status}")
        if trace.context:
            print(f"  Context: {trace.context.source}")


if __name__ == "__main__":
    main()
"""

print("This example requires LangGraph. Install it with:")
print("  pip install langgraph langchain-openai")
print("\nThen uncomment the code in this file to run it.")
