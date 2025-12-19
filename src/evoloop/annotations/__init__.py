"""
Annotations module for EvoLoop.

Provides infrastructure for human annotation of traces following
Hamel Husain's "Critique Shadowing" methodology:
- Binary Pass/Fail judgments (not 1-5 scales)
- Detailed critiques explaining the reasoning
- Tags for failure taxonomy

This module is the bridge between raw traces and automated evaluation.
"""

from evoloop.annotations.types import (
    Annotation,
    AnnotationSet,
    Judgment,
)
from evoloop.annotations.storage import AnnotationStorage

__all__ = [
    "Annotation",
    "AnnotationSet", 
    "AnnotationStorage",
    "Judgment",
]
