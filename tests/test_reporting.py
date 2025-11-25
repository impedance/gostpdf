"""Tests for reporting helpers."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from md2pdf.reporting import StructureWarning, format_warnings, write_warnings


def test_structure_warning_format() -> None:
    warning = StructureWarning(
        code="MISSING_INDEX",
        path=Path("content/003.cu"),
        message="Отсутствует 0.index.md или index.md",
    )

    assert warning.format() == (
        "[MISSING_INDEX] content/003.cu: Отсутствует 0.index.md или index.md"
    )


def test_format_warnings_list() -> None:
    warnings = [
        StructureWarning(
            code="SKIPPED_NON_MD",
            path=Path("content/003.cu/doc"),
            message="Пропущен не-markdown файл",
        ),
        StructureWarning(
            code="NON_NUMERIC_FILE",
            path=Path("content/003.cu/readme.md"),
            message="Файл без числового префикса, порядок по алфавиту",
        ),
    ]

    assert format_warnings(warnings) == [
        "[SKIPPED_NON_MD] content/003.cu/doc: Пропущен не-markdown файл",
        "[NON_NUMERIC_FILE] content/003.cu/readme.md: "
        "Файл без числового префикса, порядок по алфавиту",
    ]


def test_write_warnings_to_stream() -> None:
    warnings = [
        StructureWarning(
            code="SKIPPED_NON_MD",
            path=Path("content/003.cu/doc"),
            message="Пропущен не-markdown файл",
        ),
    ]
    buffer = StringIO()

    write_warnings(warnings, stream=buffer)

    assert (
        buffer.getvalue()
        == "[SKIPPED_NON_MD] content/003.cu/doc: Пропущен не-markdown файл\n"
    )
