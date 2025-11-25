"""Pipeline aggregation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable, Tuple

from .reporting import StructureWarning


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Result of a pipeline run with aggregated warnings."""

    bundle_path: Path
    output_pdf: Path | None
    warnings: tuple[StructureWarning, ...]


def merge_warnings(*sources: Iterable[StructureWarning]) -> tuple[StructureWarning, ...]:
    """Combine warnings from independent pipeline stages.

    Дубликаты по тройке (code, path, message) отбрасываются, порядок
    сохраняется по первому вхождению.
    """

    merged: list[StructureWarning] = []
    seen: set[Tuple[str, Path, str]] = set()

    for warning in chain.from_iterable(sources):
        key = (warning.code, warning.path, warning.message)
        if key in seen:
            continue
        seen.add(key)
        merged.append(warning)

    return tuple(merged)


def aggregate_result(
    bundle_path: Path,
    output_pdf: Path | None,
    *warning_sources: Iterable[StructureWarning],
) -> PipelineResult:
    """Construct :class:`PipelineResult` with merged warnings."""

    return PipelineResult(
        bundle_path=bundle_path,
        output_pdf=output_pdf,
        warnings=merge_warnings(*warning_sources),
    )
