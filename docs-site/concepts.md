# Why EvoLoop? Understanding Stage 1

## The Problem

You built an AI agent. It works in some cases, but fails in others. How do you improve?

**Real-world scenarios:**

1. **"My agent gave the wrong answer to this customer."**
   - You don't know *why* it failed.
   - Can't reproduce the error systematically.
   - Without history, debugging is nearly impossible.

2. **"I updated the model version and responses got worse."**
   - No clear metric of "before vs after".
   - Don't know which questions now fail.

3. **"I need to improve my agent, but where do I start?"**
   - Without execution data, you're guessing.
   - Improvement is a shot in the dark, not optimization.

---

## The Root Cause

AI agents are **dynamic black boxes**:
- The same input can generate different outputs (temperature, model, context).
- Traditional logging captures *events*, not the **complete flow** of thought + action + result.
- Generic monitoring tools don't understand AI traces.

**Result:** You have executions, but no *data to evolve*.

---

## The Solution: EvoLoop Stage 1

EvoLoop starts simple: **capture and store agent traces in structured form**.

### What is a Trace?

A **Trace** is the complete record of an agent execution:

```json
{
    "id": "uuid-123",
    "input": "What is the balance on account 12345?",
    "output": "Your current balance is $1,500.00",
    "context": {
        "data": {
            "api_balance": 1500.00,
            "api_response_time_ms": 45
        }
    },
    "timestamp": "2025-12-18T10:30:00",
    "duration_ms": 2341.5,
    "status": "success",
    "error": null,
    "metadata": {
        "user_id": "customer_456",
        "session": "session_789",
        "model": "gpt-4o"
    }
}
```

**Why does this matter?**
- You have history of *every* execution.
- Can filter by error, by user, by time.
- Structured data ready for analysis.

---

## 3 Reasons to Use EvoLoop Now (Stage 1)

### 1. **Debug Without Guessing**

Before (without EvoLoop):
```
Customer: "Your agent gave the wrong answer!"
You: "Hmm, what was the exact question?"
Customer: "I don't remember..."
```

With EvoLoop:
```python
from evoloop import get_storage

storage = get_storage()
error_traces = storage.list_traces(status="error", limit=10)

for trace in error_traces:
    print(f"Input: {trace.input}")
    print(f"Error: {trace.error}")
    print(f"Duration: {trace.duration_ms}ms")
    # Now you have the data. Reproduce, understand, fix.
```

### 2. **Measure Impact**

Before (without EvoLoop):
```
You: "Let me increase temperature to 0.7"
Result: ???
```

With EvoLoop:
```python
# Baseline
traces_before = storage.list_traces(limit=100)
success_before = len([t for t in traces_before if t.status == "success"])
# 85% success

# Make your change
# ... (run 100 new executions)

traces_after = storage.list_traces(limit=100, offset=100)
success_after = len([t for t in traces_after if t.status == "success"])
# 92% success!

print(f"Improvement: +{success_after - success_before}%")
```

### 3. **Foundation for Evals (Phase 2)**

Stage 1 = **data capture**
Stage 2 = **automated evaluation** (LLM Judge)

Without data, you can't do evals. EvoLoop Stage 1 is the foundation.

```python
# Stage 1 (now)
traces = get_storage().list_traces(limit=100)

# Stage 2 (next)
from evoloop.judge import LLMJudge

judge = LLMJudge(
    criteria="Does the response completely answer the question?"
)

for trace in traces:
    result = judge.evaluate(trace)
    # { "passed": True/False, "reason": "...", "error_category": "..." }
```

---

## How EvoLoop Differs

| Aspect | Generic Logging | Generic Monitoring | **EvoLoop** |
|--------|---|---|---|
| **Zero Config** | ❌ (setup required) | ❌ (heavy config) | ✅ (local SQLite) |
| **Structured Traces** | ❌ (free-form strings) | ⚠️ (generic) | ✅ (Trace dataclass) |
| **Eval-Ready** | ❌ | ❌ | ✅ (integrated) |
| **No Heavy Dependencies** | ✅ | ❌ | ✅ |
| **Framework-Agnostic** | ✅ | ⚠️ (vendor lock-in) | ✅ |

---

## Typical Usage Flow

```
┌──────────────────────┐
│ Your Agent (any      │
│ framework)           │
└──────┬───────────────┘
       │
       │ Add @monitor
       ▼
┌──────────────────────┐
│ @monitor decorator   │
│ (zero code changes)  │
└──────┬───────────────┘
       │
       │ Automatically captures:
       │ - Input/Output
       │ - Timestamp
       │ - Duration
       │ - Errors
       ▼
┌──────────────────────┐
│ SQLite Local         │
│ (evoloop.db)         │
│ Persists everything  │
└──────┬───────────────┘
       │
       │ Later (analysis):
       │ - Search by status
       │ - Filter by user
       │ - Calculate metrics
       │ - Ready for ML Eval
       ▼
┌──────────────────────┐
│ Dashboard/Report     │
│ (phase 2)            │
└──────────────────────┘
```

---

## Summary

**EvoLoop Stage 1 answers:**
- ✅ "When my agent fails, why?"
- ✅ "Did my change help or hurt?"
- ✅ "Which inputs cause problems?"
- ✅ "Am I ready for automated evaluation?"

**Next:** Get started in 5 minutes → see `guide.md`
