"""
CSV export functionality for EvoLoop.

Exports traces and annotations to CSV format for analysis in 
spreadsheet applications (Excel, Google Sheets).
"""

import csv
import json
from pathlib import Path
from typing import Optional, TextIO, Union

from evoloop.storage import SQLiteStorage
from evoloop.annotations.storage import AnnotationStorage


def export_traces_to_csv(
    output: Union[str, Path, TextIO],
    storage: Optional[SQLiteStorage] = None,
    limit: int = 10000,
    status: Optional[str] = None,
    include_context: bool = True,
) -> int:
    """
    Export traces to CSV format.
    
    Args:
        output: File path or file-like object to write to.
        storage: Storage instance. Uses default if not provided.
        limit: Maximum number of traces to export.
        status: Filter by status ("success" or "error").
        include_context: Whether to include context column.
    
    Returns:
        Number of traces exported.
    
    Example:
        >>> from evoloop.export import export_traces_to_csv
        >>> count = export_traces_to_csv("traces.csv", limit=1000)
        >>> print(f"Exported {count} traces")
    """
    if storage is None:
        storage = SQLiteStorage()
    
    traces = storage.list_traces(limit=limit, status=status)
    
    if not traces:
        return 0
    
    # Determine columns
    columns = [
        "id",
        "timestamp",
        "status",
        "duration_ms",
        "input",
        "output",
        "error",
    ]
    if include_context:
        columns.append("context")
    columns.append("metadata")
    
    # Handle file path vs file object
    should_close = False
    if isinstance(output, (str, Path)):
        file_handle = open(output, "w", newline="", encoding="utf-8")
        should_close = True
    else:
        file_handle = output
    
    try:
        writer = csv.DictWriter(file_handle, fieldnames=columns)
        writer.writeheader()
        
        for trace in traces:
            row = {
                "id": trace.id,
                "timestamp": trace.timestamp,
                "status": trace.status,
                "duration_ms": trace.duration_ms,
                "input": _serialize_value(trace.input),
                "output": _serialize_value(trace.output),
                "error": trace.error or "",
            }
            if include_context:
                row["context"] = json.dumps(trace.context.to_dict(), ensure_ascii=False) if trace.context else ""
            row["metadata"] = json.dumps(trace.metadata, ensure_ascii=False) if trace.metadata else ""
            
            writer.writerow(row)
        
        return len(traces)
    finally:
        if should_close:
            file_handle.close()


def export_annotations_to_csv(
    output: Union[str, Path, TextIO],
    storage: Optional[AnnotationStorage] = None,
    limit: int = 10000,
    judgment: Optional[str] = None,
    include_trace_data: bool = False,
    trace_storage: Optional[SQLiteStorage] = None,
) -> int:
    """
    Export annotations to CSV format.
    
    Useful for:
    - Analyzing annotation patterns in spreadsheets
    - Sharing with domain experts for review
    - Building reports
    
    Args:
        output: File path or file-like object to write to.
        storage: AnnotationStorage instance. Uses default if not provided.
        limit: Maximum number of annotations to export.
        judgment: Filter by judgment ("pass", "fail", "skip").
        include_trace_data: Whether to include trace input/output.
        trace_storage: TraceStorage for including trace data.
    
    Returns:
        Number of annotations exported.
    
    Example:
        >>> from evoloop.export import export_annotations_to_csv
        >>> count = export_annotations_to_csv("annotations.csv", judgment="fail")
        >>> print(f"Exported {count} failed annotations")
    """
    if storage is None:
        storage = AnnotationStorage()
    
    annotations = storage.list_annotations(limit=limit, judgment=judgment)
    
    if not annotations:
        return 0
    
    # Determine columns
    columns = [
        "id",
        "trace_id",
        "judgment",
        "critique",
        "tags",
        "annotator",
        "timestamp",
    ]
    if include_trace_data:
        columns.extend(["trace_input", "trace_output"])
    
    # Handle file path vs file object
    should_close = False
    if isinstance(output, (str, Path)):
        file_handle = open(output, "w", newline="", encoding="utf-8")
        should_close = True
    else:
        file_handle = output
    
    # Load trace data if needed
    trace_cache = {}
    if include_trace_data:
        if trace_storage is None:
            trace_storage = SQLiteStorage()
        for annotation in annotations:
            trace = trace_storage.load(annotation.trace_id)
            if trace:
                trace_cache[annotation.trace_id] = trace
    
    try:
        writer = csv.DictWriter(file_handle, fieldnames=columns)
        writer.writeheader()
        
        for annotation in annotations:
            row = {
                "id": annotation.id,
                "trace_id": annotation.trace_id,
                "judgment": annotation.judgment.value,
                "critique": annotation.critique,
                "tags": ",".join(annotation.tags),
                "annotator": annotation.annotator,
                "timestamp": annotation.timestamp,
            }
            
            if include_trace_data:
                trace = trace_cache.get(annotation.trace_id)
                if trace:
                    row["trace_input"] = _serialize_value(trace.input)
                    row["trace_output"] = _serialize_value(trace.output)
                else:
                    row["trace_input"] = ""
                    row["trace_output"] = ""
            
            writer.writerow(row)
        
        return len(annotations)
    finally:
        if should_close:
            file_handle.close()


def _serialize_value(value) -> str:
    """Serialize a value to string for CSV."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)
