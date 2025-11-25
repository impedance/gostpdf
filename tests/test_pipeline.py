from pathlib import Path

import pytest

from md2pdf.pipeline import (
    MarkdownCollection,
    PipelineParams,
    collect_markdown,
    prepare_params,
)
from md2pdf.reporting import StructureWarning


def _write_config(config_path: Path, with_output: bool = True) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "content_root: content",
        "images_root: public/images",
        "style: base",
        "template: templates/gost.tex",
    ]
    if with_output:
        lines.append("output: output/report.pdf")
    lines.append("metadata:")
    lines.append("  title: 'Документ'")
    lines.append("  doctype: 'Черновик'")
    config_path.write_text("\n".join(lines), encoding="utf-8")


def _prepare_project_layout(base_dir: Path) -> tuple[Path, Path]:
    md_root = base_dir / "content" / "003.cu"
    md_root.mkdir(parents=True)

    images_root = base_dir / "public" / "images"
    images_root.mkdir(parents=True)

    styles_dir = base_dir / "styles"
    styles_dir.mkdir(parents=True)
    (styles_dir / "base.yaml").write_text("base-style", encoding="utf-8")
    (styles_dir / "alt.yaml").write_text("alt-style", encoding="utf-8")

    templates_dir = base_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "gost.tex").write_text("% template", encoding="utf-8")

    return md_root, images_root


def test_collect_markdown_returns_order(tmp_path: Path) -> None:
    md_root = tmp_path / "003.cu"
    md_root.mkdir()
    (md_root / "0.index.md").write_text("root index")
    (md_root / "010000.first.md").write_text("first")

    collection = collect_markdown(md_root)

    assert isinstance(collection, MarkdownCollection)
    assert collection.order == [
        md_root / "0.index.md",
        md_root / "010000.first.md",
    ]
    assert collection.warnings == []


def test_collect_markdown_accumulates_warnings(tmp_path: Path) -> None:
    md_root = tmp_path / "005.rosa-virt"
    md_root.mkdir()
    (md_root / "010000.some.md").write_text("content")

    existing_warning = StructureWarning(
        code="PREV_STAGE",
        path=md_root,
        message="initial warning",
    )

    collection = collect_markdown(md_root, warnings=[existing_warning])

    assert collection.order == [md_root / "010000.some.md"]
    assert collection.warnings[0] == existing_warning
    assert any(w.code == "MISSING_INDEX" for w in collection.warnings[1:])


def test_prepare_params_merges_config_and_overrides(tmp_path: Path) -> None:
    md_root, images_root = _prepare_project_layout(tmp_path)
    config_path = tmp_path / "config" / "project.yml"
    _write_config(config_path)

    params = prepare_params(
        md_dir=md_root,
        config_path=config_path,
        metadata_overrides={"title": "Override", "author": "User"},
    )

    assert isinstance(params, PipelineParams)
    assert params.md_root == md_root
    assert params.images_root == images_root
    assert params.output_pdf == tmp_path / "output" / "report.pdf"
    assert params.bundle_path == tmp_path / "output" / "report.bundle.md"
    assert params.metadata["title"] == "Override"
    assert params.metadata["doctype"] == "Черновик"
    assert params.metadata["author"] == "User"


def test_prepare_params_accepts_style_override(tmp_path: Path) -> None:
    md_root, _ = _prepare_project_layout(tmp_path)
    config_path = tmp_path / "config" / "project.yml"
    _write_config(config_path)

    params = prepare_params(
        md_dir=md_root, config_path=config_path, style_override="alt"
    )

    assert params.style == tmp_path / "styles" / "alt.yaml"


def test_prepare_params_requires_existing_md_dir(tmp_path: Path) -> None:
    _prepare_project_layout(tmp_path)
    config_path = tmp_path / "config" / "project.yml"
    _write_config(config_path)

    with pytest.raises(ValueError, match="Missing directory"):
        prepare_params(md_dir=tmp_path / "missing", config_path=config_path)


def test_prepare_params_requires_output(tmp_path: Path) -> None:
    md_root, _ = _prepare_project_layout(tmp_path)
    config_path = tmp_path / "config" / "project.yml"
    _write_config(config_path, with_output=False)

    with pytest.raises(ValueError, match="Output path must"):
        prepare_params(md_dir=md_root, config_path=config_path)


def test_prepare_params_validates_metadata_override_type(tmp_path: Path) -> None:
    md_root, _ = _prepare_project_layout(tmp_path)
    config_path = tmp_path / "config" / "project.yml"
    _write_config(config_path)

    with pytest.raises(ValueError, match="metadata overrides must be a mapping"):
        prepare_params(  # type: ignore[arg-type]
            md_dir=md_root,
            config_path=config_path,
            metadata_overrides=[("title", "bad")],
        )
