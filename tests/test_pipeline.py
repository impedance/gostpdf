from pathlib import Path

from md2pdf.pipeline import BundleArtifacts, assemble_bundle


def _fixture_order() -> list[Path]:
    base = Path(__file__).parent / "fixtures" / "bundle" / "003.cu"
    return [
        base / "0.index.md",
        base / "010000.overview.md",
        base / "01.section" / "010100.chapter.md",
    ]


def _fixture_resolver(md_root: Path):
    doc_slug = md_root.name.split(".", 1)[-1]

    def resolver(md_path: Path, image_name: str) -> Path:
        relative = md_path.relative_to(md_root)
        parents = [part.split(".", 1)[-1] for part in relative.parts[:-1]]
        return Path("/images") / doc_slug / Path(*parents) / image_name

    return resolver


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
    assert "title: \"Куратор\"" in result.content


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

    assert any("/assets/overview.png" in line for line in result.content.splitlines())
    assert calls, "custom resolver should be invoked at least once"
