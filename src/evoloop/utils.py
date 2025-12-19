"""
Utility functions for EvoLoop.

Provides robust serialization and other helper functions.
"""

import json
from datetime import datetime, date
from uuid import UUID
from typing import Any


class SafeEncoder(json.JSONEncoder):
    """
    A robust JSON encoder that never fails.
    
    Handles common Python types and falls back to string representation
    for unknown types instead of raising errors.
    
    Supports:
    - datetime/date objects
    - UUID objects
    - Pydantic models (v1 and v2)
    - Dataclasses
    - LangChain messages (duck typing)
    - Any object with __dict__
    """
    
    def default(self, obj: Any) -> Any:
        # Handle datetime/date
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Handle UUID
        if isinstance(obj, UUID):
            return str(obj)
        
        # Handle bytes
        if isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return f"<bytes: {len(obj)} bytes>"
        
        # Handle sets and frozensets
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        
        # Handle LangChain BaseMessage (duck typing to avoid import)
        if hasattr(obj, "content") and hasattr(obj, "type"):
            result = {
                "type": getattr(obj, "type", obj.__class__.__name__),
                "content": obj.content,
            }
            if hasattr(obj, "additional_kwargs"):
                result["additional_kwargs"] = obj.additional_kwargs
            if hasattr(obj, "tool_calls"):
                result["tool_calls"] = obj.tool_calls
            return result
        
        # Handle Pydantic v2 models
        if hasattr(obj, "model_dump"):
            try:
                return obj.model_dump()
            except Exception:
                pass
        
        # Handle Pydantic v1 models
        if hasattr(obj, "dict") and hasattr(obj, "__fields__"):
            try:
                return obj.dict()
            except Exception:
                pass
        
        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            try:
                from dataclasses import asdict
                return asdict(obj)
            except Exception:
                pass
        
        # Handle objects with __dict__
        if hasattr(obj, "__dict__"):
            try:
                return {
                    "__class__": obj.__class__.__name__,
                    **obj.__dict__
                }
            except Exception:
                pass
        
        # Handle generators/iterators by consuming them
        if hasattr(obj, "__iter__") and hasattr(obj, "__next__"):
            try:
                return list(obj)
            except Exception:
                return f"<iterator: {type(obj).__name__}>"
        
        # Last resort: convert to string (NEVER fails)
        try:
            return str(obj)
        except Exception:
            return f"<unserializable: {type(obj).__name__}>"


def safe_serialize(obj: Any) -> str:
    """
    Safely serialize any object to a JSON string.
    
    This function never raises an exception. If serialization fails,
    it returns a string representation of the object.
    
    Args:
        obj: Any Python object to serialize.
        
    Returns:
        A JSON string representation of the object.
    """
    try:
        return json.dumps(obj, cls=SafeEncoder, ensure_ascii=False)
    except Exception:
        # Ultimate fallback - should never happen, but just in case
        try:
            return json.dumps(str(obj))
        except Exception:
            return '"<serialization_failed>"'


def safe_deserialize(json_str: str) -> Any:
    """
    Safely deserialize a JSON string.
    
    Args:
        json_str: A JSON string to parse.
        
    Returns:
        The parsed Python object, or the original string if parsing fails.
    """
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return json_str
