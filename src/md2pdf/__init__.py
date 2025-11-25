"""md2pdf package."""

from .bundle import DEFAULT_BUNDLE_METADATA, build, write_bundle
from .config import ProjectConfig, load_config
from .images import resolve_image_path, rewrite_images, strip_numeric
from .pandoc_runner import render
from .pipeline import (
    BundleArtifacts,
    MarkdownCollection,
    PipelineParams,
    PipelineResult,
    aggregate_result,
    assemble_bundle,
    collect_markdown,
    merge_warnings,
    prepare_params,
    render_pdf,
)
from .reporting import StructureWarning, format_warnings, write_warnings
from .walker import walk

__all__ = [
    "aggregate_result",
    "BundleArtifacts",
    "DEFAULT_BUNDLE_METADATA",
    "PipelineResult",
    "ProjectConfig",
    "StructureWarning",
    "format_warnings",
    "assemble_bundle",
    "MarkdownCollection",
    "collect_markdown",
    "prepare_params",
    "PipelineParams",
    "merge_warnings",
    "build",
    "write_bundle",
    "load_config",
    "render",
    "render_pdf",
    "resolve_image_path",
    "rewrite_images",
    "strip_numeric",
    "walk",
    "write_warnings",
]
