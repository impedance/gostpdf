from __future__ import annotations

from pathlib import Path
import shutil

from md2pdf import pipeline
from md2pdf.pipeline import (
    aggregate_result,
    assemble_bundle,
    collect_markdown,
    prepare_params,
    render_pdf,
)


def test_pipeline_runs_end_to_end(monkeypatch, tmp_path):
    fixture_root = Path(__file__).parent / "fixtures" / "pipeline"
    project_root = tmp_path / "project"
    shutil.copytree(fixture_root, project_root)

    params = prepare_params(
        md_dir=project_root / "content" / "003.cu",
        config_path=project_root / "config" / "project.yml",
        metadata_overrides={"doctype": "Рабочая копия"},
        output_override=project_root / "output" / "custom.pdf",
    )

    collection = collect_markdown(params.md_root)
    render_calls: dict[str, object] = {}

    def fake_render(
        bundle_path: Path,
        style_path: Path,
        template_path: Path,
        output_path: Path,
        filter_paths: tuple[Path, ...] | list[Path] = (),
    ) -> None:
        render_calls["args"] = (
            bundle_path,
            style_path,
            template_path,
            output_path,
            tuple(filter_paths),
        )
        output_path.write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(pipeline, "_render", fake_render)

    bundle = assemble_bundle(
        collection.order,
        params.bundle_path,
        metadata=params.metadata,
    )

    output_pdf = render_pdf(
        bundle.path,
        style=params.style,
        template=params.template,
        output=params.output_pdf,
        filters=params.filters,
    )

    result = aggregate_result(bundle.path, output_pdf, collection.warnings)

    assert bundle.path == params.bundle_path
    assert output_pdf.exists()
    assert output_pdf.read_text(encoding="utf-8") == "pdf"
    assert render_calls["args"] == (
        bundle.path,
        params.style,
        params.template,
        params.output_pdf,
        params.filters,
    )

    assert "/images/cu/index/images/overview.png" in bundle.content
    assert "/images/cu/section/chapter/diagrams/flow.png" in bundle.content
    assert "/images/cu/section/chapter/signatures/dir/manager.png" in bundle.content

    assert any(warning.code == "SKIPPED_NON_MD" for warning in result.warnings)
    assert 'doctype: "Рабочая копия"' in bundle.content
    assert 'title: "Интеграционный тест"' in bundle.content
