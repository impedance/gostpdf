from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
import subprocess
from contextlib import nullcontext
from typing import IO


def render(
    bundle: Path,
    style: Path,
    template: Path,
    output: Path,
    filters: Sequence[Path] = (),
    *,
    verbose: bool = False,
    log_file: Path | None = None,
) -> None:
    """Запустить Pandoc для рендера PDF.

    Args:
        bundle: Путь до собранного markdown-бандла.
        style: YAML со стилевыми переменными для шаблона.
        template: Шаблон LaTeX для Pandoc.
        output: Итоговый путь до PDF.
        filters: Необязательные lua-фильтры.
        verbose: Если True, поток Pandoc выводится в stdout по мере выполнения.
        log_file: Файл для записи полного вывода Pandoc.

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

    env = _build_env()

    log_handle: IO[str] | None
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_file, "a", encoding="utf-8")
    else:
        log_handle = None

    with log_handle or nullcontext() as handle:
        combined_output: list[str] = []
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        assert process.stdout is not None  # for mypy
        _pipe_output(process.stdout, combined_output, verbose, handle)
        process.wait()
        return_code = process.returncode

    if return_code != 0:
        stderr = "".join(combined_output).strip()
        joined_command = " ".join(command)
        raise RuntimeError(
            f"Pandoc failed with code {return_code}: {stderr}\nCommand: {joined_command}"
        )


def _pipe_output(
    stream: IO[str],
    buffer: list[str],
    verbose: bool,
    log_handle: IO[str] | None,
) -> None:
    for line in stream:
        buffer.append(line)
        if verbose:
            print(line, end="", flush=True)
        if log_handle is not None:
            log_handle.write(line)
            log_handle.flush()


def _build_env() -> dict[str, str]:
    env = dict(os.environ)
    texmfvar = env.get("TEXMFVAR")
    if texmfvar is None:
        texmfvar_path = Path.cwd() / ".texmf-var"
        env["TEXMFVAR"] = str(texmfvar_path)
    else:
        texmfvar_path = Path(texmfvar)
    texmfvar_path.mkdir(parents=True, exist_ok=True)
    return env
