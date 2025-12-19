"""
Storage backend for annotations.

Stores annotations in SQLite alongside traces for zero-configuration setup.
All operations are fail-safe (errors logged, never raised).
"""

import json
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any, Iterator, Optional

from evoloop.annotations.types import Annotation, AnnotationSet, Judgment


def _log_error(message: str) -> None:
    """Log an error to stderr without raising."""
    print(f"[EvoLoop Annotations Warning] {message}", file=sys.stderr)


class AnnotationStorage:
    """
    SQLite-based storage for annotations.
    
    Features:
    - Zero configuration (auto-creates tables)
    - Thread-safe operations
    - Efficient querying with indexes
    - Linked to traces via trace_id
    
    Args:
        db_path: Path to SQLite database. Defaults to "evoloop.db" (same as traces).
    
    Example:
        >>> from evoloop.annotations import AnnotationStorage, Annotation, Judgment
        >>> 
        >>> storage = AnnotationStorage()
        >>> annotation = Annotation(
        ...     trace_id="trace-123",
        ...     judgment=Judgment.FAIL,
        ...     critique="Agent offered wrong discount",
        ...     tags=["wrong_discount"]
        ... )
        >>> storage.save(annotation)
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
        """Initialize the database schema for annotations."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Annotations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    judgment TEXT NOT NULL,
                    critique TEXT NOT NULL,
                    tags TEXT,
                    annotator TEXT DEFAULT 'default',
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (trace_id) REFERENCES traces(id)
                )
            """)
            
            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_trace_id 
                ON annotations(trace_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_judgment 
                ON annotations(judgment)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_annotator 
                ON annotations(annotator)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_timestamp 
                ON annotations(timestamp DESC)
            """)
            
            # Annotation sets table (for organizing review sessions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotation_sets (
                    name TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Junction table for set membership
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotation_set_members (
                    set_name TEXT NOT NULL,
                    annotation_id TEXT NOT NULL,
                    PRIMARY KEY (set_name, annotation_id),
                    FOREIGN KEY (set_name) REFERENCES annotation_sets(name),
                    FOREIGN KEY (annotation_id) REFERENCES annotations(id)
                )
            """)
            
            conn.commit()
        except Exception as e:
            _log_error(f"Failed to initialize annotations database: {e}")

    def save(self, annotation: Annotation) -> None:
        """
        Save an annotation to the database.
        
        Fail-safe: errors are logged but never raised.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            data = annotation.to_dict()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO annotations 
                (id, trace_id, judgment, critique, tags, annotator, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["trace_id"],
                    data["judgment"],
                    data["critique"],
                    json.dumps(data["tags"], ensure_ascii=False),
                    data["annotator"],
                    data["timestamp"],
                    json.dumps(data["metadata"], ensure_ascii=False) if data["metadata"] else None,
                ),
            )
            
            conn.commit()
        except Exception as e:
            _log_error(f"Failed to save annotation {annotation.id}: {e}")

    def load(self, annotation_id: str) -> Optional[Annotation]:
        """Load an annotation by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM annotations WHERE id = ?",
                (annotation_id,),
            )
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return self._row_to_annotation(row)
        except Exception as e:
            _log_error(f"Failed to load annotation {annotation_id}: {e}")
            return None

    def get_for_trace(self, trace_id: str) -> list[Annotation]:
        """Get all annotations for a specific trace."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM annotations WHERE trace_id = ? ORDER BY timestamp DESC",
                (trace_id,),
            )
            
            return [self._row_to_annotation(row) for row in cursor.fetchall()]
        except Exception as e:
            _log_error(f"Failed to get annotations for trace {trace_id}: {e}")
            return []

    def list_annotations(
        self,
        limit: int = 100,
        offset: int = 0,
        judgment: Optional[str] = None,
        annotator: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[Annotation]:
        """
        List annotations with optional filtering.
        
        Args:
            limit: Maximum number of annotations to return.
            offset: Number of annotations to skip.
            judgment: Filter by judgment ("pass", "fail", "skip").
            annotator: Filter by annotator.
            tag: Filter by tag (annotations containing this tag).
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM annotations WHERE 1=1"
            params: list = []
            
            if judgment:
                query += " AND judgment = ?"
                params.append(judgment)
            
            if annotator:
                query += " AND annotator = ?"
                params.append(annotator)
            
            if tag:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            return [self._row_to_annotation(row) for row in cursor.fetchall()]
        except Exception as e:
            _log_error(f"Failed to list annotations: {e}")
            return []

    def count(
        self,
        judgment: Optional[str] = None,
        annotator: Optional[str] = None,
    ) -> int:
        """Count annotations with optional filtering."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) FROM annotations WHERE 1=1"
            params: list = []
            
            if judgment:
                query += " AND judgment = ?"
                params.append(judgment)
            
            if annotator:
                query += " AND annotator = ?"
                params.append(annotator)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except Exception as e:
            _log_error(f"Failed to count annotations: {e}")
            return 0

    def get_unannotated_traces(self, limit: int = 50) -> list[str]:
        """
        Get trace IDs that have not been annotated yet.
        
        Useful for the annotation workflow.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT t.id FROM traces t
                LEFT JOIN annotations a ON t.id = a.trace_id
                WHERE a.id IS NULL
                ORDER BY t.timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            _log_error(f"Failed to get unannotated traces: {e}")
            return []

    def get_failure_taxonomy(self) -> dict[str, int]:
        """
        Build a failure taxonomy from all annotations.
        
        Returns tag counts sorted by frequency.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT tags FROM annotations WHERE judgment = 'fail'"
            )
            
            taxonomy: dict[str, int] = {}
            for row in cursor.fetchall():
                if row[0]:
                    tags = json.loads(row[0])
                    for tag in tags:
                        taxonomy[tag] = taxonomy.get(tag, 0) + 1
            
            return dict(sorted(taxonomy.items(), key=lambda x: x[1], reverse=True))
        except Exception as e:
            _log_error(f"Failed to get failure taxonomy: {e}")
            return {}

    def get_stats(self) -> dict[str, Any]:
        """
        Get annotation statistics.
        
        Returns pass rate, failure taxonomy, annotator breakdown, etc.
        """
        try:
            total = self.count()
            passes = self.count(judgment="pass")
            fails = self.count(judgment="fail")
            skips = self.count(judgment="skip")
            
            pass_rate = (passes / (passes + fails) * 100) if (passes + fails) > 0 else 0.0
            
            return {
                "total": total,
                "pass": passes,
                "fail": fails,
                "skip": skips,
                "pass_rate": round(pass_rate, 1),
                "failure_taxonomy": self.get_failure_taxonomy(),
            }
        except Exception as e:
            _log_error(f"Failed to get stats: {e}")
            return {}

    def iter_annotations(self) -> Iterator[Annotation]:
        """Iterate over all annotations."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM annotations ORDER BY timestamp DESC")
            
            for row in cursor:
                yield self._row_to_annotation(row)
        except Exception as e:
            _log_error(f"Failed to iterate annotations: {e}")

    def delete(self, annotation_id: str) -> bool:
        """Delete an annotation by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            _log_error(f"Failed to delete annotation {annotation_id}: {e}")
            return False

    def _row_to_annotation(self, row: sqlite3.Row) -> Annotation:
        """Convert a database row to an Annotation."""
        return Annotation(
            id=row["id"],
            trace_id=row["trace_id"],
            judgment=Judgment(row["judgment"]),
            critique=row["critique"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            annotator=row["annotator"],
            timestamp=row["timestamp"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )


# Convenience function for getting the default storage
_default_storage: Optional[AnnotationStorage] = None


def get_annotation_storage(db_path: str = "evoloop.db") -> AnnotationStorage:
    """Get the default annotation storage instance."""
    global _default_storage
    if _default_storage is None:
        _default_storage = AnnotationStorage(db_path)
    return _default_storage
