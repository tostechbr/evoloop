"""
Storage backends for EvoLoop traces.

This module provides storage implementations for persisting traces.
The default implementation uses SQLite for zero-configuration local storage.
"""

import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterator, Optional

from evoloop.types import Trace


class BaseStorage(ABC):
    """Abstract base class for trace storage backends."""

    @abstractmethod
    def save(self, trace: Trace) -> None:
        """Save a trace to storage."""
        pass

    @abstractmethod
    def load(self, trace_id: str) -> Optional[Trace]:
        """Load a trace by ID."""
        pass

    @abstractmethod
    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[Trace]:
        """List traces with optional filtering."""
        pass

    @abstractmethod
    def count(self, status: Optional[str] = None) -> int:
        """Count total traces, optionally filtered by status."""
        pass

    @abstractmethod
    def iter_traces(self) -> Iterator[Trace]:
        """Iterate over all traces."""
        pass


class SQLiteStorage(BaseStorage):
    """
    SQLite-based storage for traces.
    
    Features:
    - Zero configuration (auto-creates database file)
    - Thread-safe operations
    - Efficient querying with indexes
    - JSON serialization for complex data
    
    Args:
        db_path: Path to the SQLite database file. Defaults to "evoloop.db".
    """

    def __init__(self, db_path: str = "evoloop.db"):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                input TEXT NOT NULL,
                output TEXT NOT NULL,
                context TEXT,
                timestamp TEXT NOT NULL,
                duration_ms REAL,
                status TEXT NOT NULL DEFAULT 'success',
                error TEXT,
                metadata TEXT
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_timestamp 
            ON traces(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_status 
            ON traces(status)
        """)
        
        conn.commit()

    def save(self, trace: Trace) -> None:
        """Save a trace to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        data = trace.to_dict()
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO traces 
            (id, input, output, context, timestamp, duration_ms, status, error, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                json.dumps(data["input"], ensure_ascii=False, default=str),
                json.dumps(data["output"], ensure_ascii=False, default=str),
                json.dumps(data["context"], ensure_ascii=False) if data["context"] else None,
                data["timestamp"],
                data["duration_ms"],
                data["status"],
                data["error"],
                json.dumps(data["metadata"], ensure_ascii=False) if data["metadata"] else None,
            ),
        )
        conn.commit()

    def load(self, trace_id: str) -> Optional[Trace]:
        """Load a trace by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM traces WHERE id = ?", (trace_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_trace(row)

    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[Trace]:
        """List traces with optional filtering."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM traces"
        params: list[Any] = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_trace(row) for row in rows]

    def count(self, status: Optional[str] = None) -> int:
        """Count total traces."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT COUNT(*) FROM traces WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT COUNT(*) FROM traces")
        
        return cursor.fetchone()[0]

    def iter_traces(self) -> Iterator[Trace]:
        """Iterate over all traces."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM traces ORDER BY timestamp DESC")
        
        for row in cursor:
            yield self._row_to_trace(row)

    def _row_to_trace(self, row: sqlite3.Row) -> Trace:
        """Convert a database row to a Trace object."""
        return Trace.from_dict({
            "id": row["id"],
            "input": json.loads(row["input"]),
            "output": json.loads(row["output"]),
            "context": json.loads(row["context"]) if row["context"] else None,
            "timestamp": row["timestamp"],
            "duration_ms": row["duration_ms"],
            "status": row["status"],
            "error": row["error"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        })

    def clear(self) -> None:
        """Clear all traces from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM traces")
        conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            delattr(self._local, "connection")
