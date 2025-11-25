"""Tests for pipeline aggregation helpers."""

from __future__ import annotations

from pathlib import Path

from md2pdf.pipeline import PipelineResult, aggregate_result, merge_warnings
from md2pdf.reporting import StructureWarning


def test_merge_warnings_deduplicates_and_preserves_order() -> None:
    first = StructureWarning(
        code="MISSING_INDEX",
        path=Path("content/001.doc"),
        message="Нет индексного файла",
    )
    duplicate = StructureWarning(
        code="MISSING_INDEX",
        path=Path("content/001.doc"),
        message="Нет индексного файла",
    )
    second = StructureWarning(
        code="NON_NUMERIC_FILE",
        path=Path("content/001.doc/notes.md"),
        message="Файл без префикса",
    )

    merged = merge_warnings([first], [duplicate, second])

    assert merged == (first, second)


def test_aggregate_result_wraps_paths_and_warnings() -> None:
    bundle_path = Path("bundle.md")
    pdf_path = Path("output/report.pdf")
    warning = StructureWarning(
        code="SKIPPED_NON_MD",
        path=Path("content/001.doc/doc"),
        message="Пропущен не-markdown файл",
    )

    result = aggregate_result(bundle_path, pdf_path, [warning])

    assert isinstance(result, PipelineResult)
    assert result.bundle_path == bundle_path
    assert result.output_pdf == pdf_path
    assert result.warnings == (warning,)
