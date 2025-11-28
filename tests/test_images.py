from pathlib import Path

import pytest

from md2pdf.images import resolve_image_path, rewrite_images, strip_numeric


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("003.cu", "cu"),
        ("02.section", "section"),
        ("file", "file"),
    ],
)
def test_strip_numeric(value: str, expected: str) -> None:
    assert strip_numeric(value) == expected


def test_resolve_image_path_basic() -> None:
    md_path = Path("content/003.cu/02.section/020100.file.md")

    result = resolve_image_path(md_path, "image1.png")

    assert result == Path("/images/cu/section/file/image1.png")


def test_resolve_image_path_cert_branch() -> None:
    md_path = Path("content/002.rosa-hrom/1.cert/010000.section/010100.file.md")

    result = resolve_image_path(md_path, "image-cert.png")

    assert result == Path("/images/rosa-hrom/cert/section/file/image-cert.png")


def test_resolve_image_path_custom_root() -> None:
    md_path = Path("content/003.cu/02.section/020100.file.md")

    result = resolve_image_path(
        md_path, "image1.png", images_root=Path("public/images")
    )

    assert result == Path("public/images/cu/section/file/image1.png")


def test_resolve_image_path_ignores_index_filename() -> None:
    md_path = Path("content/003.cu/02.section/0.index.md")

    result = resolve_image_path(md_path, "image1.png")

    assert result == Path("/images/cu/section/image1.png")


def test_rewrite_markdown_image_links() -> None:
    md_path = Path("content/003.cu/02.section/020100.file.md")
    text = (
        "Intro ![Alt text](image1.png) and remote ![Skip](https://example.com/image.png) "
        "and existing ![Keep](/images/external.png)."
    )

    result = rewrite_images(md_path, text)

    assert (
        result == "Intro ![Alt text](/images/cu/section/file/image1.png) "
        "and remote ![Skip](https://example.com/image.png) and existing ![Keep](/images/external.png)."
    )


def test_rewrite_html_and_sign_images() -> None:
    md_path = Path("content/002.rosa-hrom/1.cert/010000.section/010100.file.md")
    text = (
        "::sign-image\nsrc: /signature.png\n:::\n"
        '<p><img src="/image2.png" alt="x" /> <img src="/images/existing.png"/></p>'
    )

    result = rewrite_images(md_path, text)

    assert result == (
        "![](/images/rosa-hrom/cert/section/file/signature.png)\n"
        '<p><img src="/images/rosa-hrom/cert/section/file/image2.png" alt="x" /> '
        '<img src="/images/existing.png"/></p>'
    )


def test_rewrite_sign_image_block_with_caption() -> None:
    md_path = Path("content/003.cu/02.section/020100.file.md")
    text = (
        "::sign-image\n---\nsrc: /signature.png\nsign: Рисунок 1 — Подпись\n---\n::\n"
    )

    result = rewrite_images(md_path, text)

    assert result == ("![Рисунок 1 — Подпись](/images/cu/section/file/signature.png)\n")


def test_resolve_image_path_rejects_invalid_root() -> None:
    with pytest.raises(ValueError):
        resolve_image_path(Path("/tmp/other/020100.file.md"), "image.png")


def test_rewrite_images_respects_custom_resolver() -> None:
    md_path = Path("content/003.cu/0.index.md")
    text = "![Alt](./image.png)"

    def resolver(
        current_md: Path, image: str
    ) -> Path:  # pragma: no cover - simple wrapper
        assert current_md == md_path
        return Path("/static") / image

    result = rewrite_images(md_path, text, resolver=resolver)

    assert result == "![Alt](/static/image.png)"
