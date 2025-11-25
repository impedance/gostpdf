"""Loading and validation of project configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Validated project configuration."""

    content_root: Path
    images_root: Path
    style: Path
    template: Path
    filters: tuple[Path, ...]
    metadata: Mapping[str, Any]
    output: Path | None


def load_config(config_path: Path) -> ProjectConfig:
    """Load and validate project configuration from YAML."""

    if not config_path.exists():
        raise ValueError(f"Missing file: {config_path}")
    if not config_path.is_file():
        raise ValueError(f"Expected file, got directory: {config_path}")

    data = yaml.safe_load(config_path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping")

    base_dir = _project_root(config_path)

    content_root = _require_dir(base_dir / _require_str(data, "content_root"))
    images_root = _require_dir(base_dir / _require_str(data, "images_root"))

    style_name = _require_str(data, "style")
    style_path = base_dir / "styles" / f"{style_name}.yaml"
    _ensure_file(style_path)

    template_value = _require_str(data, "template")
    template_path = base_dir / template_value
    _ensure_file(template_path)

    filters_raw = data.get("filters", [])
    filters = _validate_filters(base_dir, filters_raw)

    metadata = data.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping if provided")

    output_value = data.get("output")
    output_path = _resolve_output(base_dir, output_value)

    return ProjectConfig(
        content_root=content_root,
        images_root=images_root,
        style=style_path,
        template=template_path,
        filters=filters,
        metadata=metadata,
        output=output_path,
    )


def _project_root(config_path: Path) -> Path:
    parent = config_path.parent
    if parent.name == "config":
        return parent.parent
    return parent


def _require_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None:
        raise ValueError(f"Missing required field: {key}")
    if not isinstance(value, str):
        raise ValueError(f"Field {key} must be a string")
    return value


def _require_dir(path: Path) -> Path:
    if not path.exists():
        raise ValueError(f"Missing directory: {path}")
    if not path.is_dir():
        raise ValueError(f"Expected directory, got file: {path}")
    return path


def _ensure_file(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"Missing file: {path}")
    if not path.is_file():
        raise ValueError(f"Expected file, got directory: {path}")


def _validate_filters(base_dir: Path, raw_filters: Any) -> tuple[Path, ...]:
    if raw_filters is None:
        return ()
    if not isinstance(raw_filters, Sequence) or isinstance(raw_filters, (str, bytes)):
        raise ValueError("filters must be a list of file paths")

    validated = []
    for filter_path in raw_filters:
        if not isinstance(filter_path, str):
            raise ValueError("filters must contain only strings")
        path = base_dir / filter_path
        _ensure_file(path)
        validated.append(path)
    return tuple(validated)


def _resolve_output(base_dir: Path, output_value: Any) -> Path | None:
    if output_value is None:
        return None
    if not isinstance(output_value, str):
        raise ValueError("output must be a string path if provided")
    return base_dir / output_value
