from pathlib import Path
import subprocess
import io

import pytest

from md2pdf.pandoc_runner import PANDOC_MARKDOWN_FORMAT, render


class _StubProcess:
    def __init__(self, returncode: int = 0, output: str = "", env: dict[str, str] | None = None) -> None:
        self.returncode = returncode
        self.stdout = io.StringIO(output)
        self.env = env or {}

    def wait(self) -> None:  # pragma: no cover - simple stub
        return


def test_render_invokes_pandoc_with_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_command: list[str] = []
    captured_env: dict[str, str] = {}

    def fake_popen(cmd, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal captured_command, captured_env
        captured_command = list(cmd)
        captured_env = kwargs.get("env", {})
        return _StubProcess(output="")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

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
        PANDOC_MARKDOWN_FORMAT,
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
    assert "TEXMFVAR" in captured_env


def test_render_raises_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_popen(*args, **kwargs):  # type: ignore[no-untyped-def]
        return _StubProcess(returncode=1, output="pandoc error")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

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
        return _StubProcess()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: fake_run(*args, **kwargs))

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
        return _StubProcess()

    monkeypatch.setenv("TEXMFVAR", str(tmp_path / "cache"))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: fake_run(*args, **kwargs))

    render(Path("bundle.md"), Path("style.yaml"), Path("template.tex"), Path("out.pdf"))

    assert captured_env.get("TEXMFVAR") == str(tmp_path / "cache")
