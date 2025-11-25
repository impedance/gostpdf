from __future__ import annotations

from collections.abc import Callable
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

from md2pdf import pipeline
from md2pdf.pipeline import (
    BundleArtifacts,
    MarkdownCollection,
    PipelineParams,
    PipelineResult,
    aggregate_result,
    assemble_bundle,
    collect_markdown,
    merge_warnings,
    prepare_params,
    render_pdf,
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


def _fixture_order() -> list[Path]:
    base = Path(__file__).parent / "fixtures" / "bundle" / "003.cu"
    return [
        base / "0.index.md",
        base / "010000.overview.md",
        base / "01.section" / "010100.chapter.md",
    ]


def _fixture_resolver(md_root: Path) -> Callable[[Path, str], Path]:
    doc_slug = md_root.name.split(".", 1)[-1]

    def resolver(md_path: Path, image_name: str) -> Path:
        relative = md_path.relative_to(md_root)
        parents = [part.split(".", 1)[-1] for part in relative.parts[:-1]]
        return Path("/images") / doc_slug / Path(*parents) / image_name

    return resolver


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

    bad_overrides = cast(Any, [("title", "bad")])

    with pytest.raises(ValueError, match="metadata overrides must be a mapping"):
        prepare_params(
            md_dir=md_root,
            config_path=config_path,
            metadata_overrides=bad_overrides,
        )


def test_assemble_bundle_builds_and_writes(tmp_path: Path) -> None:
    destination = tmp_path / "bundle.md"
    md_root = Path(__file__).parent / "fixtures" / "bundle" / "003.cu"

    result = assemble_bundle(
        _fixture_order(),
        destination,
        metadata={"title": "Куратор"},
        image_resolver=_fixture_resolver(md_root),
    )

    assert isinstance(result, BundleArtifacts)
    assert result.path == destination
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == result.content
    assert 'title: "Куратор"' in result.content


def test_assemble_bundle_uses_custom_image_resolver(tmp_path: Path) -> None:
    calls: list[tuple[Path, str]] = []

    def resolver(md_path: Path, image_name: str) -> Path:
        calls.append((md_path, image_name))
        return Path("/assets") / image_name

    result = assemble_bundle(
        _fixture_order(),
        tmp_path / "bundle.md",
        image_resolver=resolver,
    )

    assert any("/assets/diagram.png" in line for line in result.content.splitlines())
    assert calls, "custom resolver should be invoked at least once"


def test_assemble_bundle_uses_images_root_when_resolver_missing(tmp_path: Path) -> None:
    destination = tmp_path / "bundle.md"
    md_root = tmp_path / "content" / "003.cu"
    source_root = Path(__file__).parent / "fixtures" / "bundle" / "003.cu"
    shutil.copytree(source_root, md_root)
    order = [
        md_root / "0.index.md",
        md_root / "010000.overview.md",
        md_root / "01.section" / "010100.chapter.md",
    ]

    result = assemble_bundle(
        order,
        destination,
        metadata={"title": "Куратор"},
        images_root=Path("public/images"),
    )

    assert "public/images/cu/overview.png" in result.content


def test_render_pdf_invokes_pandoc_runner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bundle = tmp_path / "bundle.md"
    bundle.write_text("content", encoding="utf-8")
    style = tmp_path / "style.yaml"
    style.write_text("", encoding="utf-8")
    template = tmp_path / "template.tex"
    template.write_text("", encoding="utf-8")
    output = tmp_path / "out" / "report.pdf"
    filters = [tmp_path / "first.lua", tmp_path / "second.lua"]

    captured: dict[str, object] = {}

    def fake_render(
        bundle_path: Path,
        style_path: Path,
        template_path: Path,
        output_path: Path,
        filter_paths: tuple[Path, ...] | list[Path] = (),
        verbose: bool = False,
        log_file: Path | None = None,
    ) -> None:
        captured["args"] = (
            bundle_path,
            style_path,
            template_path,
            output_path,
            tuple(filter_paths),
            verbose,
            log_file,
        )

    monkeypatch.setattr(pipeline, "_render", fake_render)

    result = render_pdf(
        bundle,
        style=style,
        template=template,
        output=output,
        filters=filters,
    )

    assert output.parent.exists()
    assert result == output
    assert captured["args"] == (
        bundle,
        style,
        template,
        output,
        tuple(filters),
        False,
        None,
    )


def test_render_pdf_validates_bundle(tmp_path: Path) -> None:
    missing_bundle = tmp_path / "missing.md"
    style = tmp_path / "style.yaml"
    style.write_text("", encoding="utf-8")
    template = tmp_path / "template.tex"
    template.write_text("", encoding="utf-8")
    output = tmp_path / "report.pdf"

    with pytest.raises(ValueError, match="Missing bundle file"):
        render_pdf(
            missing_bundle,
            style=style,
            template=template,
            output=output,
        )

    directory_bundle = tmp_path / "dir"
    directory_bundle.mkdir()

    with pytest.raises(ValueError, match="Expected file, got directory"):
        render_pdf(
            directory_bundle,
            style=style,
            template=template,
            output=output,
        )


def test_merge_warnings_deduplicates_and_preserves_order() -> None:
    first = StructureWarning(
        code="MISSING_INDEX",
        path=Path("content/001.doc"),
        message="Нет индексного файла",
    )
    duplicate = StructureWarning(
        code="MISSING_INDEX",
        path=Path("content/001.doc"),
        message="Нет индексного файла",
    )
    second = StructureWarning(
        code="NON_NUMERIC_FILE",
        path=Path("content/001.doc/notes.md"),
        message="Файл без префикса",
    )

    merged = merge_warnings([first], [duplicate, second])

    assert merged == (first, second)


def test_aggregate_result_wraps_paths_and_warnings() -> None:
    bundle_path = Path("bundle.md")
    pdf_path = Path("output/report.pdf")
    warning = StructureWarning(
        code="SKIPPED_NON_MD",
        path=Path("content/001.doc/doc"),
        message="Пропущен не-markdown файл",
    )

    result = aggregate_result(bundle_path, pdf_path, [warning])

    assert isinstance(result, PipelineResult)
    assert result.bundle_path == bundle_path
    assert result.output_pdf == pdf_path
    assert result.warnings == (warning,)
