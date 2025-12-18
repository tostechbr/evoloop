"""
EvoLoop - Self-Evolving Agent Framework

A framework-agnostic library for evaluating and improving AI agents.
"""

from evoloop.types import Trace, TraceContext
from evoloop.storage import SQLiteStorage
from evoloop.tracker import monitor, wrap, log, get_storage

__version__ = "0.1.0"

__all__ = [
    "monitor",
    "wrap", 
    "log",
    "get_storage",
    "Trace",
    "TraceContext",
    "SQLiteStorage",
]
