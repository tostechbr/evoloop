"""
Tracker module for EvoLoop.

Provides multiple ways to capture agent traces:
- @monitor: Decorator for any Python function
- wrap(): Wrapper for objects with .invoke()/.stream() methods (LangGraph, LangChain)
- log(): Manual logging for maximum control

All methods are designed to be non-intrusive and framework-agnostic.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
from contextvars import ContextVar
from typing import Any, Callable, Optional, TypeVar, Union

from evoloop.storage import BaseStorage, SQLiteStorage
from evoloop.types import Trace, TraceContext

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])

# Global storage instance (configurable)
_storage: ContextVar[Optional[BaseStorage]] = ContextVar("evoloop_storage", default=None)

# Context variable for passing additional context to traces
_current_context: ContextVar[Optional[TraceContext]] = ContextVar("evoloop_context", default=None)


def get_storage() -> BaseStorage:
    """
    Get the current storage instance.
    
    Creates a default SQLiteStorage if none is configured.
    
    Returns:
        The current storage backend.
    """
    storage = _storage.get()
    if storage is None:
        storage = SQLiteStorage()
        _storage.set(storage)
    return storage


def set_storage(storage: BaseStorage) -> None:
    """
    Set the global storage backend.
    
    Args:
        storage: A storage backend implementing BaseStorage.
    """
    _storage.set(storage)


def set_context(context: TraceContext) -> None:
    """
    Set context data for the current execution.
    
    This context will be attached to any traces captured during this execution.
    Use this to attach API responses, database queries, or other relevant data.
    
    Args:
        context: The context to attach to traces.
    
    Example:
        >>> from evoloop import set_context, TraceContext
        >>> set_context(TraceContext(data={"api_response": {"balance": 1000}}))
    """
    _current_context.set(context)


def get_context() -> Optional[TraceContext]:
    """Get the current context, if any."""
    return _current_context.get()


def clear_context() -> None:
    """Clear the current context."""
    _current_context.set(None)


def monitor(
    func: Optional[F] = None,
    *,
    name: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> F | Callable[[F], F]:
    """
    Decorator to monitor a function and capture traces.
    
    This is the primary way to add EvoLoop monitoring to any agent function.
    It captures input arguments, output results, execution time, and any errors.
    
    Supports both synchronous and asynchronous functions automatically.
    
    Args:
        func: The function to monitor (when used without parentheses).
        name: Optional name for the trace (defaults to function name).
        metadata: Optional static metadata to attach to all traces.
    
    Returns:
        The decorated function that captures traces.
    
    Example:
        >>> from evoloop import monitor
        >>> 
        >>> @monitor
        >>> def my_agent(user_message: str) -> str:
        ...     return "Hello, " + user_message
        >>> 
        >>> # With options
        >>> @monitor(name="chat_agent", metadata={"version": "1.0"})
        >>> def my_agent(user_message: str) -> str:
        ...     return "Hello, " + user_message
        >>>
        >>> # Works with async functions too!
        >>> @monitor(name="async_agent")
        >>> async def my_async_agent(query: str) -> str:
        ...     await asyncio.sleep(0.1)
        ...     return "Async response"
    """
    def decorator(fn: F) -> F:
        trace_name = name or fn.__name__
        
        # Check if function is async
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                storage = get_storage()
                start_time = time.perf_counter()
                
                # Capture input
                input_data = _capture_input(args, kwargs)
                
                # Get any context set by the user
                context = get_context()
                
                # Prepare metadata
                trace_metadata = metadata.copy() if metadata else {}
                trace_metadata["function_name"] = trace_name
                trace_metadata["is_async"] = True
                
                try:
                    # Execute the async function
                    result = await fn(*args, **kwargs)
                    
                    # Calculate duration
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Create and save trace
                    trace = Trace(
                        input=input_data,
                        output=result,
                        context=context,
                        duration_ms=duration_ms,
                        status="success",
                        metadata=trace_metadata,
                    )
                    storage.save(trace)
                    
                    return result
                    
                except Exception as e:
                    # Calculate duration even on error
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Create and save error trace
                    trace = Trace(
                        input=input_data,
                        output=None,
                        context=context,
                        duration_ms=duration_ms,
                        status="error",
                        error=str(e),
                        metadata=trace_metadata,
                    )
                    storage.save(trace)
                    
                    # Re-raise the exception
                    raise
                finally:
                    # Clear context after each call
                    clear_context()
            
            return async_wrapper  # type: ignore
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                storage = get_storage()
                start_time = time.perf_counter()
                
                # Capture input
                input_data = _capture_input(args, kwargs)
                
                # Get any context set by the user
                context = get_context()
                
                # Prepare metadata
                trace_metadata = metadata.copy() if metadata else {}
                trace_metadata["function_name"] = trace_name
                trace_metadata["is_async"] = False
                
                try:
                    # Execute the function
                    result = fn(*args, **kwargs)
                    
                    # Calculate duration
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Create and save trace
                    trace = Trace(
                        input=input_data,
                        output=result,
                        context=context,
                        duration_ms=duration_ms,
                        status="success",
                        metadata=trace_metadata,
                    )
                    storage.save(trace)
                    
                    return result
                    
                except Exception as e:
                    # Calculate duration even on error
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Create and save error trace
                    trace = Trace(
                        input=input_data,
                        output=None,
                        context=context,
                        duration_ms=duration_ms,
                        status="error",
                        error=str(e),
                        metadata=trace_metadata,
                    )
                    storage.save(trace)
                    
                    # Re-raise the exception
                    raise
                finally:
                    # Clear context after each call
                    clear_context()
            
            return sync_wrapper  # type: ignore
    
    # Handle both @monitor and @monitor() syntax
    if func is not None:
        return decorator(func)
    return decorator


def wrap(
    agent: Any,
    *,
    name: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Any:
    """
    Wrap an agent object to capture traces from .invoke() and .stream() calls.
    
    This is designed for LangGraph, LangChain, and similar frameworks that use
    the .invoke() / .stream() pattern.
    
    Args:
        agent: The agent object to wrap.
        name: Optional name for traces.
        metadata: Optional static metadata for traces.
    
    Returns:
        A wrapped agent that captures traces.
    
    Example:
        >>> from evoloop import wrap
        >>> from langgraph.prebuilt import create_react_agent
        >>> 
        >>> agent = create_react_agent(model, tools)
        >>> monitored_agent = wrap(agent, name="my_react_agent")
        >>> 
        >>> # Use as normal
        >>> result = monitored_agent.invoke({"messages": [...]})
    """
    return _AgentWrapper(agent, name=name, metadata=metadata)


class _AgentWrapper:
    """Internal wrapper class for agent objects."""
    
    def __init__(
        self,
        agent: Any,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self._agent = agent
        self._name = name or getattr(agent, "name", agent.__class__.__name__)
        self._metadata = metadata or {}
    
    def invoke(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapped invoke method with trace capture."""
        storage = get_storage()
        start_time = time.perf_counter()
        context = get_context()
        
        trace_metadata = self._metadata.copy()
        trace_metadata["agent_name"] = self._name
        trace_metadata["method"] = "invoke"
        
        try:
            result = self._agent.invoke(input_data, *args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Extract messages for LangGraph-style agents
            processed_input = self._extract_messages(input_data, "input")
            processed_output = self._extract_messages(result, "output")
            
            trace = Trace(
                input=processed_input,
                output=processed_output,
                context=context,
                duration_ms=duration_ms,
                status="success",
                metadata=trace_metadata,
            )
            storage.save(trace)
            
            return result
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            trace = Trace(
                input=self._extract_messages(input_data, "input"),
                output=None,
                context=context,
                duration_ms=duration_ms,
                status="error",
                error=str(e),
                metadata=trace_metadata,
            )
            storage.save(trace)
            raise
        finally:
            clear_context()
    
    def stream(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapped stream method with trace capture."""
        storage = get_storage()
        start_time = time.perf_counter()
        context = get_context()
        
        trace_metadata = self._metadata.copy()
        trace_metadata["agent_name"] = self._name
        trace_metadata["method"] = "stream"
        
        # Collect all streamed chunks
        chunks = []
        
        try:
            for chunk in self._agent.stream(input_data, *args, **kwargs):
                chunks.append(chunk)
                yield chunk
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Reconstruct final output from chunks
            final_output = self._reconstruct_from_chunks(chunks)
            
            trace = Trace(
                input=self._extract_messages(input_data, "input"),
                output=final_output,
                context=context,
                duration_ms=duration_ms,
                status="success",
                metadata=trace_metadata,
            )
            storage.save(trace)
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            trace = Trace(
                input=self._extract_messages(input_data, "input"),
                output={"partial_chunks": chunks} if chunks else None,
                context=context,
                duration_ms=duration_ms,
                status="error",
                error=str(e),
                metadata=trace_metadata,
            )
            storage.save(trace)
            raise
        finally:
            clear_context()
    
    async def ainvoke(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapped async invoke method with trace capture."""
        storage = get_storage()
        start_time = time.perf_counter()
        context = get_context()
        
        trace_metadata = self._metadata.copy()
        trace_metadata["agent_name"] = self._name
        trace_metadata["method"] = "ainvoke"
        
        try:
            result = await self._agent.ainvoke(input_data, *args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            trace = Trace(
                input=self._extract_messages(input_data, "input"),
                output=self._extract_messages(result, "output"),
                context=context,
                duration_ms=duration_ms,
                status="success",
                metadata=trace_metadata,
            )
            storage.save(trace)
            
            return result
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            trace = Trace(
                input=self._extract_messages(input_data, "input"),
                output=None,
                context=context,
                duration_ms=duration_ms,
                status="error",
                error=str(e),
                metadata=trace_metadata,
            )
            storage.save(trace)
            raise
        finally:
            clear_context()
    
    def _extract_messages(self, data: Any, direction: str) -> Any:
        """Extract messages from LangGraph-style state dicts."""
        if isinstance(data, dict) and "messages" in data:
            return data
        return data
    
    def _reconstruct_from_chunks(self, chunks: list[Any]) -> Any:
        """Reconstruct the final output from streamed chunks."""
        if not chunks:
            return None
        
        # For LangGraph, the last chunk usually contains the final state
        # Try to get a meaningful representation
        last_chunk = chunks[-1]
        
        # If chunks are dicts with messages, try to merge them
        if all(isinstance(c, dict) for c in chunks):
            merged = {}
            for chunk in chunks:
                for key, value in chunk.items():
                    if key not in merged:
                        # Copy the value if it's a list to avoid modifying the original chunk
                        if isinstance(value, list):
                            merged[key] = list(value)
                        else:
                            merged[key] = value
                    elif isinstance(value, list) and isinstance(merged[key], list):
                        merged[key].extend(value)
                    else:
                        merged[key] = value
            return merged
        
        return last_chunk
    
    def __getattr__(self, name: str) -> Any:
        """Proxy all other attributes to the wrapped agent."""
        return getattr(self._agent, name)


def log(
    input_data: Any,
    output_data: Any,
    *,
    context: Optional[TraceContext] = None,
    metadata: Optional[dict[str, Any]] = None,
    status: str = "success",
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
) -> Trace:
    """
    Manually log a trace.
    
    Use this for maximum control over what gets logged.
    This is useful when the decorator or wrapper approaches don't fit your use case.
    
    Args:
        input_data: The input to log.
        output_data: The output to log.
        context: Optional context data.
        metadata: Optional metadata.
        status: "success" or "error".
        error: Error message if status is "error".
        duration_ms: Execution duration in milliseconds.
    
    Returns:
        The created Trace object.
    
    Example:
        >>> from evoloop import log, TraceContext
        >>> 
        >>> # After your agent runs
        >>> trace = log(
        ...     input_data=user_message,
        ...     output_data=agent_response,
        ...     context=TraceContext(data={"api_balance": 1000}),
        ...     metadata={"user_id": "123"},
        ... )
    """
    storage = get_storage()
    
    trace = Trace(
        input=input_data,
        output=output_data,
        context=context,
        duration_ms=duration_ms,
        status=status,
        error=error,
        metadata=metadata or {},
    )
    
    storage.save(trace)
    return trace


def _capture_input(args: tuple, kwargs: dict) -> Any:
    """
    Capture function input in a serializable format.
    
    Tries to be smart about common patterns:
    - Single argument: just return it
    - Multiple args: return as list
    - Mixed: return as dict with args and kwargs
    """
    if not args and not kwargs:
        return None
    
    if len(args) == 1 and not kwargs:
        return args[0]
    
    if not args and kwargs:
        return kwargs
    
    return {
        "args": list(args),
        "kwargs": kwargs,
    }
