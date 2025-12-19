"""
Core types for the annotation system.

Following Hamel Husain's methodology:
- Binary judgments (Pass/Fail) - NOT Likert scales
- Detailed critiques that explain reasoning
- Tags for building failure taxonomy
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class Judgment(str, Enum):
    """
    Binary judgment for a trace.
    
    Following Hamel's advice:
    "Binary evaluations force clearer thinking and more consistent labeling.
    Likert scales introduce significant challenges: the difference between 
    adjacent points (like 3 vs 4) is subjective and inconsistent."
    """
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"  # For traces that can't be evaluated (incomplete, etc.)


@dataclass
class Annotation:
    """
    A human annotation on a trace.
    
    This captures the domain expert's judgment following the 
    "Critique Shadowing" methodology:
    
    1. judgment: Did the AI achieve the desired outcome? (Pass/Fail)
    2. critique: Detailed explanation of the reasoning
    3. tags: Categories for building failure taxonomy
    
    Attributes:
        id: Unique identifier for this annotation.
        trace_id: The trace being annotated.
        judgment: Binary Pass/Fail decision.
        critique: Detailed explanation (should be detailed enough for few-shot prompts).
        tags: List of tags for failure taxonomy (e.g., "wrong_discount", "hallucination").
        annotator: Who made this annotation (for multi-annotator scenarios).
        timestamp: When the annotation was made.
        metadata: Additional data (session info, etc.).
    
    Example:
        >>> annotation = Annotation(
        ...     trace_id="trace-123",
        ...     judgment=Judgment.FAIL,
        ...     critique="The AI offered a 50% discount but the max allowed is 30%. "
        ...              "This violates business rules and could cause financial loss.",
        ...     tags=["wrong_discount", "business_rule_violation"],
        ...     annotator="maria@company.com"
        ... )
    """
    trace_id: str
    judgment: Judgment
    critique: str
    id: str = field(default_factory=lambda: str(uuid4()))
    tags: list[str] = field(default_factory=list)
    annotator: str = "default"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert annotation to dictionary for storage."""
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "judgment": self.judgment.value if isinstance(self.judgment, Judgment) else self.judgment,
            "critique": self.critique,
            "tags": self.tags,
            "annotator": self.annotator,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Annotation":
        """Create an Annotation from a dictionary."""
        judgment_value = d.get("judgment", "skip")
        if isinstance(judgment_value, str):
            judgment = Judgment(judgment_value)
        else:
            judgment = judgment_value
            
        return cls(
            id=d.get("id", str(uuid4())),
            trace_id=d["trace_id"],
            judgment=judgment,
            critique=d.get("critique", ""),
            tags=d.get("tags", []),
            annotator=d.get("annotator", "default"),
            timestamp=d.get("timestamp", datetime.now().isoformat()),
            metadata=d.get("metadata", {}),
        )

    @property
    def is_pass(self) -> bool:
        """Check if this annotation is a pass."""
        return self.judgment == Judgment.PASS

    @property
    def is_fail(self) -> bool:
        """Check if this annotation is a fail."""
        return self.judgment == Judgment.FAIL


@dataclass
class AnnotationSet:
    """
    A collection of annotations, typically from a review session.
    
    Useful for:
    - Tracking annotation progress
    - Computing agreement metrics (when multiple annotators)
    - Exporting for LLM Judge training
    
    Attributes:
        name: Name of this annotation set (e.g., "sprint_23_review").
        annotations: List of annotations in this set.
        created_at: When this set was created.
        metadata: Additional info (annotator guidelines, etc.).
    """
    name: str
    annotations: list[Annotation] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def add(self, annotation: Annotation) -> None:
        """Add an annotation to the set."""
        self.annotations.append(annotation)

    @property
    def pass_count(self) -> int:
        """Count of passing annotations."""
        return sum(1 for a in self.annotations if a.is_pass)

    @property
    def fail_count(self) -> int:
        """Count of failing annotations."""
        return sum(1 for a in self.annotations if a.is_fail)

    @property
    def pass_rate(self) -> float:
        """Pass rate as a percentage."""
        total = self.pass_count + self.fail_count
        if total == 0:
            return 0.0
        return (self.pass_count / total) * 100

    def get_failure_taxonomy(self) -> dict[str, int]:
        """
        Build a failure taxonomy from tags.
        
        This is the "Axial Coding" step from Hamel's methodology:
        "Categorize the open-ended notes into a failure taxonomy.
        Group similar failures into distinct categories."
        
        Returns:
            Dictionary mapping tag names to counts.
        """
        taxonomy: dict[str, int] = {}
        for annotation in self.annotations:
            if annotation.is_fail:
                for tag in annotation.tags:
                    taxonomy[tag] = taxonomy.get(tag, 0) + 1
        return dict(sorted(taxonomy.items(), key=lambda x: x[1], reverse=True))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "annotations": [a.to_dict() for a in self.annotations],
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AnnotationSet":
        """Create from dictionary."""
        return cls(
            name=d["name"],
            annotations=[Annotation.from_dict(a) for a in d.get("annotations", [])],
            created_at=d.get("created_at", datetime.now().isoformat()),
            metadata=d.get("metadata", {}),
        )

    def export_for_judge(self) -> list[dict[str, Any]]:
        """
        Export annotations in a format suitable for LLM Judge few-shot prompts.
        
        Returns examples with trace context + judgment + critique,
        which can be used directly in judge prompts.
        """
        examples = []
        for annotation in self.annotations:
            if annotation.judgment != Judgment.SKIP:
                examples.append({
                    "trace_id": annotation.trace_id,
                    "judgment": annotation.judgment.value,
                    "critique": annotation.critique,
                    "tags": annotation.tags,
                })
        return examples
