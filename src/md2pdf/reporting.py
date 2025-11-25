"""Warnings and logging helpers for the md2pdf pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO

import sys


@dataclass(frozen=True, slots=True)
class StructureWarning:
    """Represents a soft warning discovered during traversal or validation."""

    code: str
    path: Path
    message: str

    def format(self) -> str:
        """Return a human-readable representation."""
        return f"[{self.code}] {self.path}: {self.message}"


def format_warnings(warnings: Iterable[StructureWarning]) -> list[str]:
    """Render warnings into human-readable strings."""

    return [warning.format() for warning in warnings]


def write_warnings(
    warnings: Iterable[StructureWarning], stream: TextIO = sys.stderr
) -> None:
    """Write formatted warnings to the provided text stream."""

    for line in format_warnings(warnings):
        print(line, file=stream)
