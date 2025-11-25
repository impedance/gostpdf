from pathlib import Path

from md2pdf.walker import walk


def test_order_with_index(tmp_path: Path) -> None:
    md_root = tmp_path / "003.cu"
    md_root.mkdir()
    (md_root / "0.index.md").write_text("root index")
    (md_root / "010000.first.md").write_text("first")
    (md_root / "020000.second.md").write_text("second")

    section = md_root / "01.section"
    section.mkdir()
    (section / "0.index.md").write_text("section index")
    (section / "010100.chapter.md").write_text("chapter")

    ordered, warnings = walk(md_root)

    assert ordered == [
        md_root / "0.index.md",
        md_root / "010000.first.md",
        md_root / "020000.second.md",
        section / "0.index.md",
        section / "010100.chapter.md",
    ]
    assert warnings == []


def test_missing_index_warns(tmp_path: Path) -> None:
    md_root = tmp_path / "005.rosa-virt"
    md_root.mkdir()
    (md_root / "010000.some.md").write_text("content")

    ordered, warnings = walk(md_root)

    assert ordered == [md_root / "010000.some.md"]
    assert any(w.code == "MISSING_INDEX" and w.path == md_root for w in warnings)


def test_plain_index_is_used(tmp_path: Path) -> None:
    md_root = tmp_path / "001.dev-portal-user"
    md_root.mkdir()
    (md_root / "index.md").write_text("root index")
    (md_root / "010000.section.md").write_text("section")

    ordered, warnings = walk(md_root)

    assert ordered[0] == md_root / "index.md"
    assert not any(w.code == "MISSING_INDEX" for w in warnings)


def test_skips_non_md_with_warning(tmp_path: Path) -> None:
    md_root = tmp_path / "004.dynamic-directory"
    md_root.mkdir()
    (md_root / "0.index.md").write_text("index")
    (md_root / "notes.txt").write_text("note")

    _, warnings = walk(md_root)

    assert any(
        w.code == "SKIPPED_NON_MD" and w.path.name == "notes.txt" for w in warnings
    )


def test_warns_on_non_numeric_file(tmp_path: Path) -> None:
    md_root = tmp_path / "000.dev"
    md_root.mkdir()
    (md_root / "0.index.md").write_text("index")
    (md_root / "chapter.md").write_text("content")

    _, warnings = walk(md_root)

    assert any(
        w.code == "NON_NUMERIC_FILE" and w.path.name == "chapter.md" for w in warnings
    )


def test_skips_doc_directory(tmp_path: Path) -> None:
    md_root = tmp_path / "003.cu"
    md_root.mkdir()
    (md_root / "0.index.md").write_text("index")

    doc_dir = md_root / "doc"
    doc_dir.mkdir()
    (doc_dir / "0.index.md").write_text("ignored")

    ordered, warnings = walk(md_root)

    assert ordered == [md_root / "0.index.md"]
    assert any(w.path == doc_dir and w.code == "SKIPPED_NON_MD" for w in warnings)
