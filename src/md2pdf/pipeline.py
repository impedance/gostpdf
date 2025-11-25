from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .pandoc_runner import render as _render


def render_pdf(
    bundle: Path,
    *,
    style: Path,
    template: Path,
    output: Path,
    filters: Sequence[Path] = (),
) -> Path:
    """Подготовить и вызвать рендер PDF через Pandoc.

    Args:
        bundle: Путь до записанного markdown-бандла.
        style: YAML-файл со стилевыми переменными.
        template: Шаблон LaTeX для Pandoc.
        output: Итоговый путь до PDF.
        filters: Необязательный список lua-фильтров.

    Returns:
        Путь до сгенерированного PDF.

    Raises:
        ValueError: Если бандл отсутствует или является директорией.
    """

    if not bundle.exists():
        raise ValueError(f"Missing bundle file: {bundle}")
    if not bundle.is_file():
        raise ValueError(f"Expected file, got directory: {bundle}")

    output.parent.mkdir(parents=True, exist_ok=True)
    _render(bundle, style, template, output, filters)
    return output
