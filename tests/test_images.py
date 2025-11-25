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


def test_rewrite_markdown_image_links() -> None:
    md_path = Path("content/003.cu/02.section/020100.file.md")
    text = (
        "Intro ![Alt text](image1.png) and remote ![Skip](https://example.com/image.png) "
        "and existing ![Keep](/images/external.png)."
    )

    result = rewrite_images(md_path, text)

    assert (
        result
        == "Intro ![Alt text](/images/cu/section/file/image1.png) "
        "and remote ![Skip](https://example.com/image.png) and existing ![Keep](/images/external.png)."
    )


def test_rewrite_html_and_sign_images() -> None:
    md_path = Path("content/002.rosa-hrom/1.cert/010000.section/010100.file.md")
    text = (
        "::sign-image\nsrc: /signature.png\n:::\n"
        "<p><img src=\"/image2.png\" alt=\"x\" /> <img src=\"/images/existing.png\"/></p>"
    )

    result = rewrite_images(md_path, text)

    assert result.startswith("::sign-image\nsrc: /images/rosa-hrom/cert/section/file/signature.png\n:::\n")
    assert (
        "<p><img src=\"/images/rosa-hrom/cert/section/file/image2.png\" alt=\"x\" /> "
        "<img src=\"/images/existing.png\"/></p>" in result
    )


def test_resolve_image_path_rejects_invalid_root() -> None:
    with pytest.raises(ValueError):
        resolve_image_path(Path("/tmp/other/020100.file.md"), "image.png")
