"""Pipeline helpers orchestrating content traversal and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from .reporting import StructureWarning
from .walker import walk


@dataclass(frozen=True, slots=True)
class MarkdownCollection:
    """Ordered markdown files and accumulated warnings."""

    order: List[Path]
    warnings: List[StructureWarning] = field(default_factory=list)


def collect_markdown(
    md_root: Path, warnings: Iterable[StructureWarning] | None = None
) -> MarkdownCollection:
    """Walk the markdown tree, preserving incoming warnings."""

    accumulated_warnings = list(warnings or [])
    ordered, walker_warnings = walk(md_root)
    accumulated_warnings.extend(walker_warnings)

    return MarkdownCollection(order=ordered, warnings=accumulated_warnings)
