<<<<<<< HEAD
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .config import ProjectConfig, load_config
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


def _resolve_output(
    override: Path | None, configured: Path | None
) -> Path:
    output = override or configured
    if output is None:
        raise ValueError("Output path must be provided via CLI or config")
    return output
=======
"""Pipeline helpers orchestrating content traversal and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from .reporting import StructureWarning
from .walker import walk


@dataclass(frozen=True, slots=True)
class MarkdownCollection:
    """Ordered markdown files and accumulated warnings."""

    order: List[Path]
    warnings: List[StructureWarning] = field(default_factory=list)


def collect_markdown(
    md_root: Path, warnings: Iterable[StructureWarning] | None = None
) -> MarkdownCollection:
    """Walk the markdown tree, preserving incoming warnings."""

    accumulated_warnings = list(warnings or [])
    ordered, walker_warnings = walk(md_root)
    accumulated_warnings.extend(walker_warnings)

    return MarkdownCollection(order=ordered, warnings=accumulated_warnings)
>>>>>>> origin/codex/-2
