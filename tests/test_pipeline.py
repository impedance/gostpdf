from pathlib import Path

from md2pdf.pipeline import MarkdownCollection, collect_markdown
from md2pdf.reporting import StructureWarning


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
