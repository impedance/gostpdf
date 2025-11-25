from pathlib import Path
import subprocess

import pytest

from md2pdf.pandoc_runner import render


class _StubResult:
    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr


def test_render_invokes_pandoc_with_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_command: list[str] = []

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal captured_command
        captured_command = list(args[0])
        return _StubResult()

    monkeypatch.setattr(subprocess, "run", fake_run)

    bundle = Path("bundle.md")
    style = Path("styles/style.yaml")
    template = Path("templates/gost.tex")
    output = Path("output/report.pdf")
    filters = [Path("filters/first.lua"), Path("filters/second.lua")]

    render(bundle, style, template, output, filters)

    assert captured_command == [
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
        "--lua-filter",
        str(filters[0]),
        "--lua-filter",
        str(filters[1]),
    ]


def test_render_raises_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        return _StubResult(returncode=1, stderr="pandoc error")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as excinfo:
        render(
            Path("bundle.md"), Path("style.yaml"), Path("template.tex"), Path("out.pdf")
        )

    assert "pandoc error" in str(excinfo.value)
    assert "pandoc bundle.md" in str(excinfo.value)


def test_render_sets_texmfvar(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured_env: dict[str, str] = {}

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal captured_env
        captured_env = kwargs.get("env", {})
        return _StubResult()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)

    render(Path("bundle.md"), Path("style.yaml"), Path("template.tex"), Path("out.pdf"))

    assert captured_env.get("TEXMFVAR") == str(tmp_path / ".texmf-var")
    assert (tmp_path / ".texmf-var").is_dir()


def test_render_respects_existing_texmfvar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured_env: dict[str, str] = {}

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal captured_env
        captured_env = kwargs.get("env", {})
        return _StubResult()

    monkeypatch.setenv("TEXMFVAR", str(tmp_path / "cache"))
    monkeypatch.setattr(subprocess, "run", fake_run)

    render(Path("bundle.md"), Path("style.yaml"), Path("template.tex"), Path("out.pdf"))

    assert captured_env.get("TEXMFVAR") == str(tmp_path / "cache")
