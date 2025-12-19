"""
JSON export functionality for EvoLoop.

Exports traces and annotations to JSON format for analysis in 
notebooks, APIs, or other tools.
"""

import json
from pathlib import Path
from typing import Any, Optional, TextIO, Union

from evoloop.storage import SQLiteStorage
from evoloop.annotations.storage import AnnotationStorage
from evoloop.utils import SafeEncoder


def export_traces_to_json(
    output: Union[str, Path, TextIO, None] = None,
    storage: Optional[SQLiteStorage] = None,
    limit: int = 10000,
    status: Optional[str] = None,
    indent: int = 2,
) -> Union[str, int]:
    """
    Export traces to JSON format.
    
    Args:
        output: File path, file-like object, or None to return string.
        storage: Storage instance. Uses default if not provided.
        limit: Maximum number of traces to export.
        status: Filter by status ("success" or "error").
        indent: JSON indentation level.
    
    Returns:
        If output is None, returns JSON string.
        Otherwise, returns number of traces exported.
    
    Example:
        >>> from evoloop.export import export_traces_to_json
        >>> 
        >>> # Export to file
        >>> count = export_traces_to_json("traces.json", limit=1000)
        >>> 
        >>> # Get as string
        >>> json_str = export_traces_to_json()
    """
    if storage is None:
        storage = SQLiteStorage()
    
    traces = storage.list_traces(limit=limit, status=status)
    
    data = {
        "version": "1.0",
        "type": "traces",
        "count": len(traces),
        "traces": [trace.to_dict() for trace in traces],
    }
    
    if output is None:
        return json.dumps(data, cls=SafeEncoder, indent=indent, ensure_ascii=False)
    
    # Handle file path vs file object
    should_close = False
    if isinstance(output, (str, Path)):
        file_handle = open(output, "w", encoding="utf-8")
        should_close = True
    else:
        file_handle = output
    
    try:
        json.dump(data, file_handle, cls=SafeEncoder, indent=indent, ensure_ascii=False)
        return len(traces)
    finally:
        if should_close:
            file_handle.close()


def export_annotations_to_json(
    output: Union[str, Path, TextIO, None] = None,
    storage: Optional[AnnotationStorage] = None,
    limit: int = 10000,
    judgment: Optional[str] = None,
    include_trace_data: bool = False,
    trace_storage: Optional[SQLiteStorage] = None,
    indent: int = 2,
) -> Union[str, int]:
    """
    Export annotations to JSON format.
    
    Particularly useful for:
    - Creating few-shot examples for LLM Judge
    - Sharing annotations with other systems
    - Backup and restore
    
    Args:
        output: File path, file-like object, or None to return string.
        storage: AnnotationStorage instance. Uses default if not provided.
        limit: Maximum number of annotations to export.
        judgment: Filter by judgment ("pass", "fail", "skip").
        include_trace_data: Whether to include trace input/output.
        trace_storage: TraceStorage for including trace data.
        indent: JSON indentation level.
    
    Returns:
        If output is None, returns JSON string.
        Otherwise, returns number of annotations exported.
    
    Example:
        >>> from evoloop.export import export_annotations_to_json
        >>> 
        >>> # Export failures for judge training
        >>> json_str = export_annotations_to_json(
        ...     judgment="fail",
        ...     include_trace_data=True
        ... )
    """
    if storage is None:
        storage = AnnotationStorage()
    
    annotations = storage.list_annotations(limit=limit, judgment=judgment)
    
    # Load trace data if needed
    trace_cache: dict[str, Any] = {}
    if include_trace_data:
        if trace_storage is None:
            trace_storage = SQLiteStorage()
        for annotation in annotations:
            trace = trace_storage.load(annotation.trace_id)
            if trace:
                trace_cache[annotation.trace_id] = trace.to_dict()
    
    # Build export data
    annotations_data = []
    for annotation in annotations:
        annotation_dict = annotation.to_dict()
        if include_trace_data and annotation.trace_id in trace_cache:
            annotation_dict["trace"] = trace_cache[annotation.trace_id]
        annotations_data.append(annotation_dict)
    
    data = {
        "version": "1.0",
        "type": "annotations",
        "count": len(annotations),
        "stats": storage.get_stats() if annotations else {},
        "annotations": annotations_data,
    }
    
    if output is None:
        return json.dumps(data, cls=SafeEncoder, indent=indent, ensure_ascii=False)
    
    # Handle file path vs file object
    should_close = False
    if isinstance(output, (str, Path)):
        file_handle = open(output, "w", encoding="utf-8")
        should_close = True
    else:
        file_handle = output
    
    try:
        json.dump(data, file_handle, cls=SafeEncoder, indent=indent, ensure_ascii=False)
        return len(annotations)
    finally:
        if should_close:
            file_handle.close()


def export_for_judge_training(
    output: Union[str, Path, TextIO, None] = None,
    storage: Optional[AnnotationStorage] = None,
    trace_storage: Optional[SQLiteStorage] = None,
    limit: int = 1000,
) -> Union[str, int]:
    """
    Export annotations in a format optimized for LLM Judge training.
    
    Creates a dataset of examples that can be used as few-shot prompts
    or fine-tuning data for an LLM-as-Judge.
    
    The format follows Hamel's recommendation:
    - Each example has input, output, judgment, and detailed critique
    - Critiques are detailed enough for a "new employee" to understand
    
    Args:
        output: File path, file-like object, or None to return string.
        storage: AnnotationStorage instance.
        trace_storage: TraceStorage instance.
        limit: Maximum number of examples.
    
    Returns:
        If output is None, returns JSON string.
        Otherwise, returns number of examples exported.
    
    Example:
        >>> from evoloop.export.json_export import export_for_judge_training
        >>> 
        >>> # Export for judge training
        >>> export_for_judge_training("judge_training_data.json")
    """
    if storage is None:
        storage = AnnotationStorage()
    if trace_storage is None:
        trace_storage = SQLiteStorage()
    
    # Get annotations (exclude skips)
    pass_annotations = storage.list_annotations(limit=limit // 2, judgment="pass")
    fail_annotations = storage.list_annotations(limit=limit // 2, judgment="fail")
    
    examples = []
    
    for annotation in pass_annotations + fail_annotations:
        trace = trace_storage.load(annotation.trace_id)
        if not trace:
            continue
        
        example = {
            "input": trace.input,
            "output": trace.output,
            "context": trace.context.to_dict() if trace.context else None,
            "judgment": annotation.judgment.value,
            "critique": annotation.critique,
            "tags": annotation.tags,
        }
        examples.append(example)
    
    data = {
        "version": "1.0",
        "type": "judge_training",
        "description": "Training data for LLM-as-Judge following Hamel Husain's Critique Shadowing methodology",
        "count": len(examples),
        "pass_count": len(pass_annotations),
        "fail_count": len(fail_annotations),
        "examples": examples,
    }
    
    if output is None:
        return json.dumps(data, cls=SafeEncoder, indent=2, ensure_ascii=False)
    
    # Handle file path vs file object
    should_close = False
    if isinstance(output, (str, Path)):
        file_handle = open(output, "w", encoding="utf-8")
        should_close = True
    else:
        file_handle = output
    
    try:
        json.dump(data, file_handle, cls=SafeEncoder, indent=2, ensure_ascii=False)
        return len(examples)
    finally:
        if should_close:
            file_handle.close()
