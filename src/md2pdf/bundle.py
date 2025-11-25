from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .images import rewrite_images

DEFAULT_BUNDLE_METADATA: Mapping[str, str] = {
    "title": "Документ",
    "doctype": "Неизвестно",
    "date": "1970-01-01",
}


def build(
    order: Sequence[Path],
    image_resolver: Callable[[Path, str], Path],
    metadata: Mapping[str, Any] | None = None,
) -> str:
    """Собрать итоговый markdown-бандл.

    Args:
        order: Упорядоченный список markdown-файлов.
        image_resolver: Колбэк резолва пути картинки относительно markdown.
        metadata: Дополнительные значения для фронтматтера бандла.

    Returns:
        Текст бандла с фронтматтером и проставленными заголовками.
    """

    merged_metadata: dict[str, Any] = {**DEFAULT_BUNDLE_METADATA}
    if metadata:
        merged_metadata.update(metadata)

    bundle_parts: list[str] = [_render_front_matter(merged_metadata)]

    if not order:
        return "\n".join(bundle_parts) + "\n"

    base_root = order[0].parent

    for md_path in order:
        raw = md_path.read_text(encoding="utf-8")
        metadata, body = _split_front_matter(raw)
        rewritten_body = rewrite_images(md_path, body, resolver=image_resolver)
        heading_level = _heading_level(base_root, md_path)
        title = metadata.get("title", _derive_title(md_path))
        section = _render_section(title, rewritten_body, heading_level)
        bundle_parts.append(section)

    return "\n\n".join(part for part in bundle_parts if part.strip()) + "\n"


def write_bundle(text: str, path: Path | str) -> Path:
    """Записать содержимое бандла в файл, создавая директории при необходимости."""

    bundle_path = Path(path)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(text, encoding="utf-8")
    return bundle_path


def _render_front_matter(metadata: Mapping[str, Any]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f'{key}: "{value}"')
    lines.append("---")
    return "\n".join(lines)


def _split_front_matter(text: str) -> tuple[Mapping[str, str], str]:
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_index: int | None = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = idx
            break

    if end_index is None:
        return {}, text

    meta_lines = lines[1:end_index]
    body_lines = lines[end_index + 1 :]
    metadata = _parse_simple_yaml(meta_lines)
    body = "\n".join(body_lines).lstrip("\n")
    return metadata, body


def _parse_simple_yaml(lines: Sequence[str]) -> Mapping[str, str]:
    metadata: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def _heading_level(base_root: Path, md_path: Path) -> int:
    try:
        relative = md_path.relative_to(base_root)
    except ValueError:
        return 1

    depth = max(len(relative.parents) - 1, 0)
    return min(depth + 1, 6)


def _derive_title(md_path: Path) -> str:
    stripped = _strip_numeric(md_path.stem)
    return stripped.replace("-", " ").replace("_", " ")


def _strip_numeric(stem: str) -> str:
    return stem.split(".", 1)[-1] if "." in stem else stem


def _render_section(title: str, body: str, level: int) -> str:
    heading_prefix = "#" * max(1, min(level, 6))
    section_parts = [f"{heading_prefix} {title}".rstrip()]
    body_content = body.strip()
    if body_content:
        section_parts.append(body_content)
    return "\n\n".join(section_parts)
