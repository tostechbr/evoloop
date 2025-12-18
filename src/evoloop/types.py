"""
Core data types for EvoLoop.

These dataclasses represent the fundamental structures used throughout the framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass
class TraceContext:
    """
    Additional context captured alongside the trace.
    
    This can include API responses, database queries, or any other
    data that was available during the agent execution.
    
    Attributes:
        data: A dictionary containing any contextual data.
        source: Optional identifier for where this context came from.
    """
    data: dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TraceContext":
        return cls(
            data=d.get("data", {}),
            source=d.get("source"),
        )


@dataclass
class Trace:
    """
    Represents a single interaction trace from an agent.
    
    A trace captures the input, output, and context of an agent execution,
    forming the foundation for evaluation and analysis.
    
    Attributes:
        id: Unique identifier for this trace.
        input: The input provided to the agent (user message, query, etc.).
        output: The output produced by the agent (response, action, etc.).
        context: Optional contextual data available during execution.
        timestamp: When this trace was captured.
        duration_ms: How long the execution took in milliseconds.
        status: Whether the execution succeeded or failed.
        error: Error message if status is "error".
        metadata: Additional metadata (user_id, session_id, tags, etc.).
    """
    input: Any
    output: Any
    id: str = field(default_factory=lambda: str(uuid4()))
    context: Optional[TraceContext] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: Optional[float] = None
    status: str = "success"  # "success" | "error"
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to a dictionary for storage."""
        return {
            "id": self.id,
            "input": self._serialize(self.input),
            "output": self._serialize(self.output),
            "context": self.context.to_dict() if self.context else None,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Trace":
        """Create a Trace from a dictionary."""
        return cls(
            id=d.get("id", str(uuid4())),
            input=d.get("input"),
            output=d.get("output"),
            context=TraceContext.from_dict(d["context"]) if d.get("context") else None,
            timestamp=d.get("timestamp", datetime.now().isoformat()),
            duration_ms=d.get("duration_ms"),
            status=d.get("status", "success"),
            error=d.get("error"),
            metadata=d.get("metadata", {}),
        )

    @staticmethod
    def _serialize(obj: Any) -> Any:
        """
        Serialize complex objects to JSON-compatible format.
        
        Handles LangChain messages, Pydantic models, and other common types.
        """
        # Handle None
        if obj is None:
            return None
        
        # Handle basic types
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        # Handle lists
        if isinstance(obj, list):
            return [Trace._serialize(item) for item in obj]
        
        # Handle dicts
        if isinstance(obj, dict):
            return {k: Trace._serialize(v) for k, v in obj.items()}
        
        # Handle LangChain BaseMessage (duck typing to avoid import)
        if hasattr(obj, "content") and hasattr(obj, "type"):
            return {
                "type": getattr(obj, "type", obj.__class__.__name__),
                "content": obj.content,
                "additional_kwargs": getattr(obj, "additional_kwargs", {}),
            }
        
        # Handle Pydantic models
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        
        # Fallback to string representation
        return str(obj)
