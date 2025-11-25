from pathlib import Path

import pytest

from md2pdf import pipeline


def test_render_pdf_invokes_pandoc_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.md"
    bundle.write_text("content", encoding="utf-8")
    style = tmp_path / "style.yaml"
    style.write_text("", encoding="utf-8")
    template = tmp_path / "template.tex"
    template.write_text("", encoding="utf-8")
    output = tmp_path / "out" / "report.pdf"
    filters = [tmp_path / "first.lua", tmp_path / "second.lua"]

    captured: dict[str, object] = {}

    def fake_render(bundle_path: Path, style_path: Path, template_path: Path, output_path: Path, filter_paths: tuple[Path, ...] | list[Path] = ()) -> None:
        captured["args"] = (bundle_path, style_path, template_path, output_path, tuple(filter_paths))

    monkeypatch.setattr(pipeline, "_render", fake_render)

    result = pipeline.render_pdf(bundle, style=style, template=template, output=output, filters=filters)

    assert output.parent.exists()
    assert result == output
    assert captured["args"] == (bundle, style, template, output, tuple(filters))


def test_render_pdf_validates_bundle(tmp_path: Path) -> None:
    missing_bundle = tmp_path / "missing.md"
    style = tmp_path / "style.yaml"
    style.write_text("", encoding="utf-8")
    template = tmp_path / "template.tex"
    template.write_text("", encoding="utf-8")
    output = tmp_path / "report.pdf"

    with pytest.raises(ValueError, match="Missing bundle file"):
        pipeline.render_pdf(missing_bundle, style=style, template=template, output=output)

    directory_bundle = tmp_path / "dir"
    directory_bundle.mkdir()

    with pytest.raises(ValueError, match="Expected file, got directory"):
        pipeline.render_pdf(directory_bundle, style=style, template=template, output=output)
