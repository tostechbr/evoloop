"""
EvoLoop - Self-Evolving Agent Framework

A framework-agnostic library for evaluating and improving AI agents.

Stage 1 Features:
- @monitor: Decorator to capture traces from any function (sync or async)
- wrap(): Wrapper for LangGraph/LangChain agents
- log(): Manual trace logging for maximum control
- SQLite storage with zero configuration

The library is designed to be non-intrusive:
- Supports both sync and async functions
- Robust serialization that never fails (Pydantic, dataclasses, LangChain messages)
- Fail-safe storage (errors are logged, never raised)
"""

from evoloop.types import Trace, TraceContext
from evoloop.storage import SQLiteStorage
from evoloop.tracker import monitor, wrap, log, get_storage, set_storage, set_context

__version__ = "0.2.0"

__all__ = [
    # Core decorators/functions
    "monitor",
    "wrap", 
    "log",
    # Storage
    "get_storage",
    "set_storage",
    "SQLiteStorage",
    # Types
    "Trace",
    "TraceContext",
    # Context
    "set_context",
]
