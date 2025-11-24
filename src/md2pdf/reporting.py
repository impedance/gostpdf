"""Warnings and logging helpers for the md2pdf pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StructureWarning:
    """Represents a soft warning discovered during traversal or validation."""

    code: str
    path: Path
    message: str

    def format(self) -> str:
        """Return a human-readable representation."""
        return f"[{self.code}] {self.path}: {self.message}"
