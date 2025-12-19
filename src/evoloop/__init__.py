"""
EvoLoop - Self-Evolving Agent Framework

A framework-agnostic library for evaluating and improving AI agents.

Phase 1 Features (Tracker):
- @monitor: Decorator to capture traces from any function (sync or async)
- wrap(): Wrapper for LangGraph/LangChain agents
- log(): Manual trace logging for maximum control
- SQLite storage with zero configuration

Phase 1.5 Features (Viewer & Annotations):
- Annotation types: Pass/Fail judgments with critiques
- Export: CSV/JSON export for analysis
- UI: Visual trace viewer and annotator (pip install evoloop[ui])
- CLI: evoloop ui, evoloop stats, evoloop export

The library is designed to be non-intrusive:
- Supports both sync and async functions
- Robust serialization that never fails (Pydantic, dataclasses, LangChain messages)
- Fail-safe storage (errors are logged, never raised)
"""

from evoloop.types import Trace, TraceContext
from evoloop.storage import SQLiteStorage
from evoloop.tracker import monitor, wrap, log, get_storage, set_storage, set_context

# Annotations (Phase 1.5)
from evoloop.annotations import Annotation, AnnotationStorage, Judgment

# Export (Phase 1.5)
from evoloop.export import (
    export_traces_to_csv,
    export_traces_to_json,
    export_annotations_to_csv,
    export_annotations_to_json,
)

__version__ = "0.3.0"

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
    # Annotations (Phase 1.5)
    "Annotation",
    "AnnotationStorage",
    "Judgment",
    # Export (Phase 1.5)
    "export_traces_to_csv",
    "export_traces_to_json",
    "export_annotations_to_csv",
    "export_annotations_to_json",
]
