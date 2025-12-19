# EvoLoop

**EvoLoop** is a framework-agnostic Python library designed to bring **Self-Evolving capabilities** to any AI Agent or LLM workflow.

Unlike other frameworks that focus on *building* agents (like LangChain, CrewAI, or Agno), EvoLoop focuses exclusively on **evaluating and optimizing** them. It acts as a "gym" for your agents, providing tools to capture interactions, evaluate performance, and learn from mistakes.

## ✨ Features

- **Framework Agnostic**: Works with LangChain, LangGraph, AutoGen, raw OpenAI API, or any other stack
- **Zero Configuration**: Just add a decorator and start capturing traces
- **Async Support**: Works seamlessly with both sync and async functions
- **Robust Serialization**: Handles Pydantic models, dataclasses, LangChain messages automatically
- **Fail-Safe**: Tracing errors are logged but never crash your application
- **Lightweight**: No heavy dependencies, SQLite storage by default
- **Multiple Integration Modes**: Decorator, wrapper, or manual logging
- **Visual UI**: Streamlit-based trace viewer for domain experts (`evoloop ui`)
- **Annotations**: Pass/Fail judgments with detailed critiques
- **Export**: CSV/JSON export for analysis in notebooks or spreadsheets

## 📦 Installation

```bash
pip install evoloop
```

With UI (for visual trace viewer):
```bash
pip install evoloop[ui]
```

Or install from source:

```bash
git clone https://github.com/tostechbr/evoloop.git
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

### Option 1b: Async Functions (Also Works!)

```python
from evoloop import monitor
import asyncio

@monitor(name="async_agent")
async def my_async_agent(question: str) -> str:
    # Your async agent logic
    await asyncio.sleep(0.1)
    return "Async response"

# Works seamlessly with async
response = await my_async_agent("What is 2+2?")
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

### Via Code

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

### Visual UI (Recommended)

Launch the Streamlit-based trace viewer:

```bash
evoloop ui
```

This opens a browser with:
- **📋 Traces**: Browse and filter all captured traces
- **✏️ Annotate**: Review traces with Pass/Fail judgments + critiques
- **📊 Stats**: View annotation progress and error taxonomy

The UI is designed for domain experts who don't need to write code.

## 📝 Annotations

Annotate traces programmatically or via the UI:

```python
from evoloop.annotations import AnnotationStorage, Annotation, Judgment

storage = AnnotationStorage()

# Add annotation
annotation = Annotation(
    trace_id="trace-123",
    judgment=Judgment.FAIL,
    critique="Response didn't address the user's main question",
    annotator="domain_expert@company.com",
    tags=["off-topic", "incomplete"]
)
storage.save(annotation)

# Get stats
stats = storage.get_stats()
print(f"Pass rate: {stats.pass_count / stats.total_count:.1%}")
```

## 📤 Export

Export traces and annotations for analysis:

```bash
# Export to CSV
evoloop export --format csv --output traces.csv

# Export to JSON
evoloop export --format json --output traces.json

# Export annotations only
evoloop export --format csv --output annotations.csv --annotations-only
```

Or via code:

```python
from evoloop.export import export_traces_to_csv, export_annotations_to_json

export_traces_to_csv("traces.csv")
export_annotations_to_json("annotations.json")
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
  - Sync and async function support
  - Robust serialization (Pydantic, dataclasses, LangChain)
  - Fail-safe storage (errors logged, never raised)
- [x] **Phase 1.5**: Visual Trace Viewer
  - Streamlit UI for domain experts
  - Pass/Fail annotations with critiques
  - CSV/JSON export for analysis
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
