# EvoLoop Stage 1 Practical Guide

Get started capturing agent traces in 5 minutes.

---

## Installation

```bash
pip install evoloop
```

Or locally (for development):
```bash
git clone https://github.com/tostechbr/evoloop.git
cd evoloop
pip install -e .
```

---

## 3 Ways to Use

### Way 1: `@monitor` Decorator (Recommended for Quick Start)

**Best for:** Simple functions, custom agents

```python
from evoloop import monitor

@monitor
def my_agent(user_question: str) -> str:
    # Your code here (OpenAI, local LLM, rules, etc)
    return "Agent response"

# Use normally — EvoLoop captures everything automatically
response = my_agent("What is the capital of France?")
print(response)  # "Paris"
```

**Captured automatically:**
- `input`: `"What is the capital of France?"`
- `output`: `"Paris"`
- `timestamp`: `"2025-12-18T10:30:00.123456"`
- `duration_ms`: `245.3`
- `status`: `"success"` or `"error"`
- `error`: message if it fails

#### With Metadata (optional)

```python
@monitor(name="geography_agent", metadata={"version": "1.0", "env": "prod"})
def my_agent(question: str) -> str:
    return "response"
```

#### With Context (API/DB data)

```python
from evoloop import monitor, set_context
from evoloop.types import TraceContext

@monitor
def debt_agent(customer_id: str) -> str:
    # Fetch data
    customer = fetch_from_api(customer_id)
    balance = get_balance(customer_id)
    
    # Attach context
    set_context(TraceContext(
        data={
            "customer": customer,
            "balance": balance,
            "api_response_time_ms": 45
        },
        source="customer_api"
    ))
    
    # Your logic
    response = f"Balance: ${balance}"
    return response
```

---

### Way 2: `wrap()` for LangGraph/LangChain

**Best for:** LangGraph or LangChain agents with `.invoke()`

```python
from evoloop import wrap
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Your LangGraph agent
model = ChatOpenAI(model="gpt-4o-mini")
tools = [...]  # your tools
agent = create_react_agent(model, tools)

# Wrap with EvoLoop
monitored = wrap(agent, name="react_agent")

# Use as before
result = monitored.invoke({
    "messages": [{"role": "user", "content": "Your question"}]
})
```

---

### Way 3: Manual `log()` (Maximum Control)

**Best for:** Complex pipelines, detailed debugging

```python
from evoloop import log
from evoloop.types import TraceContext

# Your agent, your logic
input_msg = "What's 2+2?"
output = run_custom_agent(input_msg)

# Log manually
trace = log(
    input_data=input_msg,
    output_data=output,
    context=TraceContext(data={"calc_time_ms": 12}),
    metadata={"user": "user_123", "session": "s_456"},
    status="success",
    duration_ms=123.5
)

print(f"Trace saved: {trace.id}")
```

---

## View Traces

### List Recent Executions

```python
from evoloop import get_storage

storage = get_storage()

# Last 10
recent = storage.list_traces(limit=10)
for trace in recent:
    print(f"[{trace.status}] {trace.input[:60]}...")
    print(f"  Duration: {trace.duration_ms}ms")
    if trace.error:
        print(f"  Error: {trace.error}")
```

### Filter by Status

```python
# Errors only
errors = storage.list_traces(status="error", limit=20)
for trace in errors:
    print(f"❌ {trace.input}")
    print(f"   Error: {trace.error}\n")

# Success only
success = storage.list_traces(status="success")
```

### Count Stats

```python
total = storage.count()
error_count = storage.count(status="error")
success_count = storage.count(status="success")

print(f"Total: {total} | Success: {success_count} | Errors: {error_count}")
success_rate = (success_count / total * 100) if total > 0 else 0
print(f"Success Rate: {success_rate:.1f}%")
```

### Iterate All Traces

```python
for trace in storage.iter_traces():
    print(f"{trace.timestamp} | {trace.input} → {trace.output}")
```

---

## Complete Example: Q&A Agent

```python
import os
from evoloop import monitor, get_storage
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@monitor(name="qa_agent", metadata={"model": "gpt-4o-mini"})
def answer_question(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        temperature=0.2
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # Run some questions
    questions = [
        "What is EvoLoop?",
        "How to install Python?",
        "What is the capital of Brazil?"
    ]
    
    for q in questions:
        answer = answer_question(q)
        print(f"Q: {q}")
        print(f"A: {answer}\n")
    
    # Analyze traces
    storage = get_storage()
    print(f"\n--- Analysis ---")
    print(f"Total executions: {storage.count()}")
    
    for trace in storage.list_traces():
        print(f"✅ {trace.input[:40]}... ({trace.duration_ms}ms)")
```

**Output:**
```
Q: What is EvoLoop?
A: EvoLoop is a Python library for...

Q: How to install Python?
A: To install Python...

Q: What is the capital of Brazil?
A: The capital of Brazil is Brasília.

--- Analysis ---
Total executions: 3
✅ What is EvoLoop?... (1245ms)
✅ How to install Python?... (892ms)
✅ What is the capital of Brazil?... (654ms)
```

---

## Where is Data Stored?

EvoLoop uses **local SQLite** by default:

```
your_project/
├── evoloop.db          ← Database file (auto-created)
├── your_agent.py
└── ...
```

**To inspect:**
```bash
sqlite3 evoloop.db
sqlite> SELECT input, output, status FROM traces LIMIT 5;
```

---

## Custom Database Path

```python
from evoloop import set_storage
from evoloop.storage import SQLiteStorage

# Use database elsewhere
custom_storage = SQLiteStorage(db_path="/var/data/my_agent.db")
set_storage(custom_storage)

# Now @monitor uses this database
```

---

## Troubleshooting

### "No traces are being saved"

1. Make sure you're using `@monitor`:
   ```python
   @monitor  # ← Don't forget!
   def my_function():
       pass
   ```

2. Call the function *before* querying:
   ```python
   my_function("test")  # ← Execute first
   storage = get_storage()  # ← Then query
   ```

3. Check if `evoloop.db` was created:
   ```bash
   ls -la evoloop.db
   ```

### "ImportError: No module named 'evoloop'"

Install correctly:
```bash
pip install evoloop
# or (if developing)
pip install -e /path/to/evoloop
```

### "Is @monitor slowing down my agent?"

No, the decorator has near-zero overhead. If something changed:
- Check for extra logging/prints in your code
- Use `duration_ms` from the trace to measure before/after

---

## Next Steps

✅ **Stage 1 (now):** You have structured traces in SQLite.

🔜 **Stage 2 (coming):** Add automated evaluation with LLM Judge.
   - Define criteria (e.g., "Is the answer clear?")
   - LLM Judge evaluates each trace
   - Error report generation

🔜 **Stage 3+:** Automatic prompt optimization, trend analysis, etc.

---

## Real-World Example (Recommended)

For a complete project with LangGraph integration, see the separate demo repo:
- **Project:** `evoloop_langgraph_demo`
- **Reference:** See `docs/langgraph-mini-project.md` in the EvoLoop repo
- **Contains:** Fully instrumented ReAct agent + integration tests

---

## API Reference

### Decorators & Functions

```python
from evoloop import monitor, wrap, log, get_storage, set_storage, set_context

# Decorator
@monitor(name="agent_name", metadata={...})
def my_agent(input: str) -> str: ...

# Wrapper
monitored = wrap(agent, name="agent_name", metadata={...})

# Manual logging
trace = log(input_data, output_data, context=..., metadata=..., ...)

# Query
storage = get_storage()
traces = storage.list_traces(limit=10, offset=0, status="success")
trace = storage.load(trace_id)
count = storage.count(status="error")

# Context
set_context(TraceContext(data={...}, source="..."))
```

### Types

```python
from evoloop.types import Trace, TraceContext

# Trace attributes
trace.id
trace.input
trace.output
trace.context  # Optional[TraceContext]
trace.timestamp
trace.duration_ms
trace.status  # "success" or "error"
trace.error  # Optional[str]
trace.metadata
```

---

## Support

- **Issues:** https://github.com/tostechbr/evoloop/issues
- **Concepts:** See `concepts.md` for the "why"
- **Examples:** `examples/` folder in main repo
