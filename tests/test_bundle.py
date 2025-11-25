from pathlib import Path
from textwrap import dedent

from md2pdf.bundle import DEFAULT_BUNDLE_METADATA, build


def _strip_numeric(stem: str) -> str:
    return stem.split(".", 1)[-1] if "." in stem else stem


def _make_resolver(md_root: Path):
    doc_slug = _strip_numeric(md_root.name)

    def resolver(md_path: Path, image_name: str) -> Path:
        relative = md_path.relative_to(md_root)
        parents = [_strip_numeric(part) for part in relative.parts[:-1]]
        return Path("/images") / doc_slug / Path(*parents) / image_name

    return resolver


def test_builds_bundle_with_front_matter_and_titles() -> None:
    md_root = Path(__file__).parent / "fixtures" / "bundle" / "003.cu"
    order = [
        md_root / "0.index.md",
        md_root / "010000.overview.md",
        md_root / "01.section" / "010100.chapter.md",
    ]

    resolver = _make_resolver(md_root)
    output = build(order, resolver)

    expected = (
        dedent(
            f"""
        ---
        title: \"{DEFAULT_BUNDLE_METADATA["title"]}\"
        doctype: \"{DEFAULT_BUNDLE_METADATA["doctype"]}\"
        date: \"{DEFAULT_BUNDLE_METADATA["date"]}\"
        ---

        # Общее описание

        Вводная часть.

        ![Схема](/images/cu/overview.png)

        # Обзор возможностей

        Текст раздела с картинкой ![Диаграмма](/images/cu/diagram.png) и ещё текст.

        ## Подраздел

        Содержимое раздела.

        <img src="/images/cu/section/signature.png" alt="Подпись" />
        """
        ).strip()
        + "\n"
    )

    assert output == expected
