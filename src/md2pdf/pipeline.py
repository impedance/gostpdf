"""Pipeline helpers for assembling intermediate artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .bundle import build as build_bundle_text
from .bundle import write_bundle
from .images import resolve_image_path


@dataclass(frozen=True, slots=True)
class BundleArtifacts:
    """Container for a rendered bundle and its location on disk."""

    path: Path
    content: str


def assemble_bundle(
    order: Sequence[Path],
    destination: Path,
    *,
    metadata: Mapping[str, Any] | None = None,
    image_resolver: Callable[[Path, str], Path] | None = None,
) -> BundleArtifacts:
    """Собрать и записать итоговый markdown-бандл."""

    resolver = image_resolver or resolve_image_path
    content = build_bundle_text(order, resolver, metadata)
    bundle_path = write_bundle(content, destination)
    return BundleArtifacts(path=bundle_path, content=content)
