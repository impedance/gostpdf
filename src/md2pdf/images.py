"""Utilities for resolving and rewriting image paths."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Callable


def strip_numeric(stem: str) -> str:
    """Remove numeric prefix separated by the first dot.

    Examples:
    - "003.cu" -> "cu"
    - "02.section" -> "section"
    - "file" -> "file"
    """

    return stem.split(".", 1)[-1] if "." in stem else stem


def resolve_image_path(md_path: Path, image_name: str) -> Path:
    """Map a markdown file and image name to an absolute images path.

    The resulting path mirrors the markdown location without numeric prefixes
    and is rooted at ``/images``. ``image_name`` may start with slashes, which
    are ignored for resolution.
    """

    image = image_name.lstrip("/")
    parts = list(md_path.with_suffix("").parts)

    try:
        content_index = parts.index("content")
    except ValueError as error:
        raise ValueError(f"Invalid markdown path: {md_path}") from error

    relevant = parts[content_index:]
    if len(relevant) < 2:
        raise ValueError(f"Invalid markdown path: {md_path}")

    stripped = [strip_numeric(part) for part in relevant]
    doc_slug = stripped[1]
    relative = stripped[2:]

    return Path("/images") / doc_slug / Path(*relative) / image


def _rewrite_markdown_image(md_path: Path, match: re.Match[str]) -> str:
    alt = match.group("alt")
    target = match.group("path")
    title = match.group("title")

    if target.startswith(("http://", "https://", "/images/")):
        return match.group(0)

    resolved = resolve_image_path(md_path, target.lstrip("./"))
    title_suffix = f' "{title}"' if title else ""
    return f"![{alt}]({resolved}{title_suffix})"


def _rewrite_html_image(md_path: Path, match: re.Match[str]) -> str:
    prefix = match.group("prefix")
    src = match.group("src")
    suffix = match.group("suffix")

    if src.startswith(("http://", "https://", "/images/")):
        return match.group(0)

    resolved = resolve_image_path(md_path, src.lstrip("./"))
    return f"{prefix}{resolved}{suffix}"


def _rewrite_sign_image(md_path: Path, match: re.Match[str]) -> str:
    src = match.group("src")
    resolved = resolve_image_path(md_path, src.lstrip("/"))
    return match.group(0).replace(src, str(resolved))


def rewrite_images(md_path: Path, text: str) -> str:
    """Rewrite image links in markdown text to absolute ``/images`` paths."""

    markdown_pattern = re.compile(
        r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"(?P<title>[^\"]*)\")?\)",
    )
    html_pattern = re.compile(
        r"(?P<prefix><img[^>]*?src=[\"'])(?P<src>[^\"']+)(?P<suffix>[\"'][^>]*?>)",
        flags=re.IGNORECASE,
    )
    sign_pattern = re.compile(r"::sign-image\s+src:\s*(?P<src>\S+)")

    transformers: list[tuple[re.Pattern[str], Callable[[Path, re.Match[str]], str]]] = [
        (sign_pattern, _rewrite_sign_image),
        (markdown_pattern, _rewrite_markdown_image),
        (html_pattern, _rewrite_html_image),
    ]

    updated = text
    for pattern, replacer in transformers:
        updated = pattern.sub(lambda m: replacer(md_path, m), updated)

    return updated
