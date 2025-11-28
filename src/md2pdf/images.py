"""Utilities for resolving and rewriting image paths."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable


def strip_numeric(stem: str) -> str:
    """Remove numeric prefix separated by the first dot.

    Examples:
    - "003.cu" -> "cu"
    - "02.section" -> "section"
    - "file" -> "file"
    """

    return stem.split(".", 1)[-1] if "." in stem else stem


def resolve_image_path(
    md_path: Path, image_name: str, images_root: Path | str = Path("/images")
) -> Path:
    """Map a markdown file and image name to an images path under ``images_root``.

    The resulting path mirrors the markdown location without numeric prefixes
    and is rooted at ``images_root``. ``image_name`` may start with slashes,
    which are ignored for resolution unless the target is already rooted under
    ``images_root``.
    """

    base = Path(images_root)
    original = Path(image_name)

    if original.is_absolute():
        return original

    normalized = image_name.lstrip("/")
    base_prefix = base.as_posix().lstrip("/")

    if base_prefix and (
        normalized == base_prefix or normalized.startswith(f"{base_prefix}/")
    ):
        prefix = "/" if str(base).startswith("/") else ""
        return Path(prefix + normalized)

    image = normalized
    parts = list(md_path.with_suffix("").parts)

    try:
        content_index = parts.index("content")
    except ValueError as error:
        raise ValueError(f"Invalid markdown path: {md_path}") from error

    relevant = parts[content_index:]
    if len(relevant) < 2:
        raise ValueError(f"Invalid markdown path: {md_path}")

    stripped = [strip_numeric(part) for part in relevant]
    if stripped and stripped[-1] == "index":
        stripped = stripped[:-1]
    doc_slug = stripped[1]
    relative = stripped[2:]

    return base / doc_slug / Path(*relative) / image


def _rewrite_markdown_image(
    md_path: Path, match: re.Match[str], resolver: Callable[[Path, str], Path]
) -> str:
    alt = match.group("alt")
    target = match.group("path")
    title = match.group("title")

    if target.startswith(("http://", "https://", "/images/")):
        return match.group(0)

    resolved = resolver(md_path, target.lstrip("./"))
    title_suffix = f' "{title}"' if title else ""
    return f"![{alt}]({resolved}{title_suffix})"


def _rewrite_html_image(
    md_path: Path, match: re.Match[str], resolver: Callable[[Path, str], Path]
) -> str:
    prefix = match.group("prefix")
    src = match.group("src")
    suffix = match.group("suffix")

    if src.startswith(("http://", "https://", "/images/")):
        return match.group(0)

    resolved = resolver(md_path, src.lstrip("./"))
    return f"{prefix}{resolved}{suffix}"


def _render_sign_image(resolved: Path, caption: str, has_trailing_newline: bool) -> str:
    suffix = "\n" if has_trailing_newline else ""
    return f"![{caption}]({resolved}){suffix}"


def _parse_sign_metadata(block: str) -> tuple[str | None, str]:
    metadata: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    src = metadata.get("src")
    caption = metadata.get("sign", "")
    return src, caption


def _rewrite_sign_block(
    md_path: Path, match: re.Match[str], resolver: Callable[[Path, str], Path]
) -> str:
    src, caption = _parse_sign_metadata(match.group("meta"))
    if src is None:
        return match.group(0)

    resolved = resolver(md_path, src.lstrip("/"))
    return _render_sign_image(resolved, caption, match.group(0).endswith("\n"))


def _rewrite_sign_inline(
    md_path: Path, match: re.Match[str], resolver: Callable[[Path, str], Path]
) -> str:
    src = match.group("src")
    resolved = resolver(md_path, src.lstrip("/"))
    return _render_sign_image(resolved, "", match.group(0).endswith("\n"))


def rewrite_images(
    md_path: Path,
    text: str,
    *,
    resolver: Callable[[Path, str], Path] | None = None,
) -> str:
    """Rewrite image links in markdown text to absolute ``/images`` paths.

    A custom ``resolver`` may be provided to alter how image targets are
    rewritten, defaulting to :func:`resolve_image_path`.
    """

    image_resolver = resolver or resolve_image_path

    markdown_pattern = re.compile(
        r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"(?P<title>[^\"]*)\")?\)",
    )
    html_pattern = re.compile(
        r"(?P<prefix><img[^>]*?src=[\"'])(?P<src>[^\"']+)(?P<suffix>[\"'][^>]*?>)",
        flags=re.IGNORECASE,
    )
    sign_block_pattern = re.compile(
        r"::sign-image\s*\n---\s*\n(?P<meta>.+?)\n---\s*\n::",
        flags=re.DOTALL,
    )
    sign_inline_pattern = re.compile(
        r"::sign-image(?:\s+|\s*\n)src:\s*(?P<src>\S+)(?:\s*\n:::+)?",
    )

    transformers: list[tuple[re.Pattern[str], Callable[[Path, re.Match[str]], str]]] = [
        (sign_block_pattern, lambda md, m: _rewrite_sign_block(md, m, image_resolver)),
        (
            sign_inline_pattern,
            lambda md, m: _rewrite_sign_inline(md, m, image_resolver),
        ),
        (
            markdown_pattern,
            lambda md, m: _rewrite_markdown_image(md, m, image_resolver),
        ),
        (html_pattern, lambda md, m: _rewrite_html_image(md, m, image_resolver)),
    ]

    updated = text
    for pattern, replacer in transformers:
        updated = pattern.sub(lambda m: replacer(md_path, m), updated)

    return updated
