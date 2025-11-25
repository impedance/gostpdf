from __future__ import annotations

from pathlib import Path

import pytest

from md2pdf import cli
from md2pdf.pipeline import BundleArtifacts, MarkdownCollection, PipelineParams
from md2pdf.reporting import StructureWarning


def test_main_runs_pipeline_and_writes_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    warning = StructureWarning(
        code="MISSING_INDEX",
        path=Path("content/003.cu"),
        message="Нет индексного файла",
    )

    params = PipelineParams(
        md_root=Path("content/003.cu"),
        images_root=Path("public/images"),
        style=Path("styles/alt.yaml"),
        template=Path("templates/gost.tex"),
        filters=(Path("filters/first.lua"),),
        metadata={"title": "Документ"},
        bundle_path=Path("bundle.md"),
        output_pdf=Path("output/report.pdf"),
    )

    captured: dict[str, object] = {}

    def fake_prepare_params(**kwargs):
        captured["prepare"] = kwargs
        return params

    def fake_collect_markdown(md_root: Path):
        captured["collect"] = md_root
        return MarkdownCollection(order=[Path("0.index.md")], warnings=[warning])

    def fake_assemble_bundle(order: list[Path], destination: Path, *, metadata: dict[str, str]):
        captured["assemble"] = (order, destination, metadata)
        return BundleArtifacts(path=destination, content="content")

    def fake_render_pdf(bundle: Path, *, style: Path, template: Path, output: Path, filters: tuple[Path, ...] | list[Path] = ()):  # type: ignore[override]
        captured["render"] = (bundle, style, template, output, tuple(filters))
        return output

    warnings_written: list[StructureWarning] = []

    def fake_write_warnings(warnings: list[StructureWarning]):
        warnings_written.extend(warnings)

    monkeypatch.setattr(cli.pipeline, "prepare_params", fake_prepare_params)
    monkeypatch.setattr(cli.pipeline, "collect_markdown", fake_collect_markdown)
    monkeypatch.setattr(cli.pipeline, "assemble_bundle", fake_assemble_bundle)
    monkeypatch.setattr(cli.pipeline, "render_pdf", fake_render_pdf)
    monkeypatch.setattr(cli, "write_warnings", fake_write_warnings)

    exit_code = cli.main(
        [
            "--md-dir",
            "content/003.cu",
            "--config",
            "config/project.yml",
            "--style",
            "alt",
            "--metadata",
            "title=Override",
            "output/report.pdf",
        ]
    )

    assert exit_code == 0
    assert captured["prepare"] == {
        "md_dir": Path("content/003.cu"),
        "config_path": Path("config/project.yml"),
        "style_override": "alt",
        "output_override": Path("output/report.pdf"),
        "metadata_overrides": {"title": "Override"},
    }
    assert captured["collect"] == params.md_root
    assert captured["assemble"] == ([Path("0.index.md")], params.bundle_path, params.metadata)
    assert captured["render"] == (
        params.bundle_path,
        params.style,
        params.template,
        params.output_pdf,
        params.filters,
    )

    assert warnings_written == [warning]


def test_main_rejects_bad_metadata(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Avoid filesystem validation when metadata parsing fails early.
    monkeypatch.setattr(cli.pipeline, "prepare_params", pytest.fail)  # type: ignore[arg-type]

    exit_code = cli.main(["--md-dir", "content/003.cu", "--metadata", "bad", "output.pdf"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "metadata overrides must use key=value format" in captured.err
