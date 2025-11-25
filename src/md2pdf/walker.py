"""Traverse markdown trees respecting numeric prefixes and gather warnings."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from .reporting import StructureWarning

INDEX_NAMES = {"0.index.md", "index.md"}


def walk(md_root: Path) -> Tuple[List[Path], List[StructureWarning]]:
    """Return ordered markdown files and collected structure warnings.

    The traversal follows the documented hierarchy rules:
    - index files (0.index.md or index.md) go первыми на уровне;
    - остальные .md сортируются по числовому префиксу, затем по имени;
    - поддиректории сортируются по числовому префиксу и обходятся рекурсивно.

    Warnings are produced for missing index files, skipped non-md files,
    and files without numeric prefixes (кроме index).
    """

    if not md_root.exists():
        raise ValueError(f"Missing directory: {md_root}")
    if not md_root.is_dir():
        raise ValueError(f"Expected directory, got file: {md_root}")

    ordered: List[Path] = []
    warnings: List[StructureWarning] = []

    def recurse(directory: Path) -> None:
        files, subdirs, skipped = _partition_entries(directory)
        for skipped_entry in skipped:
            warnings.append(
                StructureWarning(
                    code="SKIPPED_NON_MD",
                    path=skipped_entry,
                    message="Пропущен не-markdown файл",
                )
            )

        index = _select_index(files)
        if index is None:
            warnings.append(
                StructureWarning(
                    code="MISSING_INDEX",
                    path=directory,
                    message="Отсутствует 0.index.md или index.md",
                )
            )
        else:
            ordered.append(index)

        for file in _sort_md(files, index):
            ordered.append(file)
            if _numeric_prefix(file.name) is None:
                warnings.append(
                    StructureWarning(
                        code="NON_NUMERIC_FILE",
                        path=file,
                        message="Файл без числового префикса, порядок по алфавиту",
                    )
                )

        for subdir in _sort_dirs(subdirs):
            recurse(subdir)

    recurse(md_root)
    return ordered, warnings


def _partition_entries(directory: Path) -> Tuple[List[Path], List[Path], List[Path]]:
    files: List[Path] = []
    dirs: List[Path] = []
    skipped: List[Path] = []
    for entry in directory.iterdir():
        if entry.is_dir():
            if entry.name == "doc":
                skipped.append(entry)
                continue
            dirs.append(entry)
            continue
        if entry.suffix.lower() == ".md":
            files.append(entry)
        else:
            skipped.append(entry)
    return files, dirs, skipped


def _select_index(files: Sequence[Path]) -> Path | None:
    prioritized = sorted(
        INDEX_NAMES, key=lambda name: 0 if name.startswith("0.") else 1
    )
    by_name = {file.name: file for file in files}
    for name in prioritized:
        if name in by_name:
            return by_name[name]
    return None


def _numeric_prefix(name: str) -> int | None:
    stem = name.split(".", 1)[0]
    return int(stem) if stem.isdigit() else None


def _sort_md(files: Sequence[Path], index: Path | None) -> List[Path]:
    def sort_key(path: Path) -> tuple[int, str]:
        num = _numeric_prefix(path.name)
        return (0, f"{num:09d}") if num is not None else (1, path.name)

    filtered = [file for file in files if file != index]
    return sorted(filtered, key=sort_key)


def _sort_dirs(dirs: Iterable[Path]) -> List[Path]:
    def sort_key(path: Path) -> tuple[int, str]:
        num = _numeric_prefix(path.name)
        return (0, f"{num:09d}") if num is not None else (1, path.name)

    return sorted(dirs, key=sort_key)
