"""Pipeline helpers orchestrating content traversal and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence, Tuple

from .bundle import build as build_bundle_text
from .bundle import write_bundle
from .config import ProjectConfig, load_config
from .images import resolve_image_path
from .pandoc_runner import render as _render
from .reporting import StructureWarning
from .walker import walk


@dataclass(frozen=True, slots=True)
class PipelineParams:
    """Aggregated and validated parameters for running the pipeline."""

    md_root: Path
    images_root: Path
    style: Path
    template: Path
    filters: tuple[Path, ...]
    metadata: Mapping[str, Any]
    bundle_path: Path
    output_pdf: Path


@dataclass(frozen=True, slots=True)
class MarkdownCollection:
    """Ordered markdown files and accumulated warnings."""

    order: list[Path]
    warnings: list[StructureWarning] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class BundleArtifacts:
    """Container for a rendered bundle and its location on disk."""

    path: Path
    content: str


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Result of a pipeline run with aggregated warnings."""

    bundle_path: Path
    output_pdf: Path | None
    warnings: tuple[StructureWarning, ...]


def prepare_params(
    md_dir: Path,
    config_path: Path,
    *,
    style_override: str | None = None,
    output_override: Path | None = None,
    metadata_overrides: Mapping[str, Any] | None = None,
    bundle_path: Path | None = None,
) -> PipelineParams:
    """Validate inputs and merge configuration with CLI overrides."""

    config = load_config(config_path)
    _ensure_directory(md_dir)

    style_path = _resolve_style(config, style_override)
    merged_metadata = _merge_metadata(config.metadata, metadata_overrides)
    output_pdf = _resolve_output(output_override, config.output)
    resolved_bundle = bundle_path or output_pdf.with_suffix(".bundle.md")

    return PipelineParams(
        md_root=md_dir,
        images_root=config.images_root,
        style=style_path,
        template=config.template,
        filters=config.filters,
        metadata=merged_metadata,
        bundle_path=resolved_bundle,
        output_pdf=output_pdf,
    )


def collect_markdown(
    md_root: Path, warnings: Iterable[StructureWarning] | None = None
) -> MarkdownCollection:
    """Walk the markdown tree, preserving incoming warnings."""

    accumulated_warnings = list(warnings or [])
    ordered, walker_warnings = walk(md_root)
    accumulated_warnings.extend(walker_warnings)

    return MarkdownCollection(order=ordered, warnings=accumulated_warnings)


def assemble_bundle(
    order: Sequence[Path],
    destination: Path,
    *,
    metadata: Mapping[str, Any] | None = None,
    image_resolver: Callable[[Path, str], Path] | None = None,
    images_root: Path | str | None = None,
    params: PipelineParams | None = None,
) -> BundleArtifacts:
    """Собрать и записать итоговый markdown-бандл.

    Если ``image_resolver`` не указан, используется :func:`resolve_image_path`
    с базой ``images_root`` (по умолчанию значение из конфига или ``/images``).
    """

    resolved_images_root = _resolve_images_root(images_root, params)
    resolver = image_resolver or (
        lambda md_path, image: resolve_image_path(
            md_path, image, resolved_images_root
        )
    )
    content = build_bundle_text(order, resolver, metadata)
    bundle_path = write_bundle(content, destination)
    return BundleArtifacts(path=bundle_path, content=content)


def render_pdf(
    bundle: Path,
    *,
    style: Path,
    template: Path,
    output: Path,
    filters: Sequence[Path] = (),
    verbose: bool = False,
    log_file: Path | None = None,
) -> Path:
    """Подготовить и вызвать рендер PDF через Pandoc."""

    if not bundle.exists():
        raise ValueError(f"Missing bundle file: {bundle}")
    if not bundle.is_file():
        raise ValueError(f"Expected file, got directory: {bundle}")

    output.parent.mkdir(parents=True, exist_ok=True)
    _render(
        bundle,
        style,
        template,
        output,
        filters,
        verbose=verbose,
        log_file=log_file,
    )
    return output


def _ensure_directory(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"Missing directory: {path}")
    if not path.is_dir():
        raise ValueError(f"Expected directory, got file: {path}")


def _resolve_style(config: ProjectConfig, override: str | None) -> Path:
    if not override:
        return config.style

    if not isinstance(override, str):
        raise ValueError("style override must be a string")

    style_path = config.style.parent / f"{override}.yaml"
    if not style_path.exists():
        raise ValueError(f"Missing file: {style_path}")
    if not style_path.is_file():
        raise ValueError(f"Expected file, got directory: {style_path}")
    return style_path


def _merge_metadata(
    config_metadata: Mapping[str, Any], overrides: Mapping[str, Any] | None
) -> Mapping[str, Any]:
    merged: dict[str, Any] = dict(config_metadata)
    if overrides is None:
        return merged
    if not isinstance(overrides, Mapping):
        raise ValueError("metadata overrides must be a mapping")
    merged.update(overrides)
    return merged


def _resolve_output(override: Path | None, configured: Path | None) -> Path:
    output = override or configured
    if output is None:
        raise ValueError("Output path must be provided via CLI or config")
    return output


def _resolve_images_root(
    images_root: Path | str | None, params: PipelineParams | None
) -> Path:
    if images_root is not None:
        return Path(images_root)
    if params is not None:
        return params.images_root
    return Path("/images")


def merge_warnings(
    *sources: Iterable[StructureWarning],
) -> tuple[StructureWarning, ...]:
    """Combine warnings from independent pipeline stages."""

    merged: list[StructureWarning] = []
    seen: set[Tuple[str, Path, str]] = set()

    for warning in chain.from_iterable(sources):
        key = (warning.code, warning.path, warning.message)
        if key in seen:
            continue
        seen.add(key)
        merged.append(warning)

    return tuple(merged)


def aggregate_result(
    bundle_path: Path,
    output_pdf: Path | None,
    *warning_sources: Iterable[StructureWarning],
) -> PipelineResult:
    """Construct pipeline result with merged warnings."""

    return PipelineResult(
        bundle_path=bundle_path,
        output_pdf=output_pdf,
        warnings=merge_warnings(*warning_sources),
    )
