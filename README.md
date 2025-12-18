# EvoLoop

**EvoLoop** is a framework-agnostic Python library designed to bring **Self-Evolving capabilities** to any AI Agent or LLM workflow.

Unlike other frameworks that focus on *building* agents (like LangChain, CrewAI, or Agno), EvoLoop focuses exclusively on **evaluating and optimizing** them. It acts as a "gym" for your agents, providing tools to capture interactions, evaluate performance, and learn from mistakes.

## ✨ Features

- **Framework Agnostic**: Works with LangChain, LangGraph, AutoGen, raw OpenAI API, or any other stack
- **Zero Configuration**: Just add a decorator and start capturing traces
- **Lightweight**: No heavy dependencies, SQLite storage by default
- **Multiple Integration Modes**: Decorator, wrapper, or manual logging

## 📦 Installation

```bash
pip install evoloop
```

Or install from source:

```bash
git clone https://github.com/yourusername/evoloop.git
cd evoloop
pip install -e .
```

## 🚀 Quick Start

### Option 1: Decorator (Simplest)

```python
from evoloop import monitor

@monitor
def my_agent(question: str) -> str:
    # Your agent logic here
    return "Agent response"

# Use as normal - traces are captured automatically
response = my_agent("What is the capital of France?")
```

### Option 2: Wrapper (For LangGraph/LangChain)

```python
from evoloop import wrap
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model, tools)
monitored_agent = wrap(agent, name="my_agent")

# Use as normal
result = monitored_agent.invoke({"messages": [...]})
```

### Option 3: Manual Logging

```python
from evoloop import log

# After your agent runs
trace = log(
    input_data=user_question,
    output_data=agent_response,
    metadata={"user_id": "123"}
)
```

## 📊 Viewing Traces

```python
from evoloop import get_storage

storage = get_storage()

# Get recent traces
traces = storage.list_traces(limit=10)
for trace in traces:
    print(f"[{trace.status}] {trace.input[:50]}...")

# Count by status
print(f"Total: {storage.count()}")
print(f"Errors: {storage.count(status='error')}")
```

## 🎯 Adding Context (Business Rules)

Attach context data for evaluation against business rules:

```python
from evoloop import monitor
from evoloop.tracker import set_context
from evoloop.types import TraceContext

@monitor
def debt_agent(user_message: str, customer_data: dict) -> str:
    # Attach API data as context
    set_context(TraceContext(
        data=customer_data,
        source="customer_api"
    ))
    
    # Agent logic...
    return response
```

## 🛣️ Roadmap

- [x] **Phase 1**: Tracker Module (capture traces)
- [ ] **Phase 2**: Judge Module (binary evaluation)
- [ ] **Phase 3**: Reporter Module (error taxonomy)
- [ ] **Phase 4**: CLI (`evoloop eval`, `evoloop report`)
- [ ] **Phase 5**: Self-Evolution (prompt optimization)

## 📚 Philosophy

EvoLoop is inspired by the principles in ["LLM Evals: Everything You Need to Know"](https://hamel.dev/blog/posts/evals-faq/) by Hamel Husain:

- **Binary evaluations** (Pass/Fail) over Likert scales (1-5)
- **Error analysis** as the core of improvement
- **Domain-specific criteria** over generic metrics

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/evoloop

# Linting
ruff check src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
