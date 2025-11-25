from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import subprocess


def render(
    bundle: Path,
    style: Path,
    template: Path,
    output: Path,
    filters: Sequence[Path] = (),
) -> None:
    """Запустить Pandoc для рендера PDF.

    Args:
        bundle: Путь до собранного markdown-бандла.
        style: YAML со стилевыми переменными для шаблона.
        template: Шаблон LaTeX для Pandoc.
        output: Итоговый путь до PDF.
        filters: Необязательные lua-фильтры.

    Raises:
        RuntimeError: Если Pandoc завершился с ошибкой.
    """

    command = [
        "pandoc",
        str(bundle),
        "--from",
        "markdown+yaml_metadata_block",
        "--template",
        str(template),
        "--pdf-engine",
        "xelatex",
        "--toc",
        "--metadata-file",
        str(style),
        "--output",
        str(output),
    ]

    for lua_filter in filters:
        command.extend(["--lua-filter", str(lua_filter)])

    result = subprocess.run(  # noqa: S603
        command, capture_output=True, text=True, check=False
    )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        joined_command = " ".join(command)
        raise RuntimeError(
            f"Pandoc failed with code {result.returncode}: {stderr}\nCommand: {joined_command}"
        )
