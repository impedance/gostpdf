"""Command-line interface for rendering Markdown trees to PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping, Sequence

from . import pipeline
from .reporting import write_warnings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Markdown content into a PDF using project configuration.",
    )
    parser.add_argument(
        "--md-dir",
        required=True,
        type=Path,
        help="Path to the markdown directory to render.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/project.yml"),
        help="Path to the project configuration file (default: config/project.yml).",
    )
    parser.add_argument(
        "--style",
        help="Override style name to resolve styles/<name>.yaml instead of config default.",
    )
    parser.add_argument(
        "--metadata",
        "-m",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override bundle metadata; can be provided multiple times.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="Destination PDF path; overrides value from config if provided.",
    )
    return parser


def _parse_metadata(pairs: Sequence[str] | None) -> Mapping[str, str]:
    overrides: dict[str, str] = {}

    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError("metadata overrides must use key=value format")
        key, value = pair.split("=", 1)
        if not key:
            raise ValueError("metadata override key must not be empty")
        overrides[key] = value

    return overrides


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        metadata_overrides = _parse_metadata(args.metadata)
        params = pipeline.prepare_params(
            md_dir=args.md_dir,
            config_path=args.config,
            style_override=args.style,
            output_override=args.output,
            metadata_overrides=metadata_overrides,
        )

        collection = pipeline.collect_markdown(params.md_root)
        bundle = pipeline.assemble_bundle(
            collection.order,
            params.bundle_path,
            metadata=params.metadata,
        )
        output_pdf = pipeline.render_pdf(
            bundle.path,
            style=params.style,
            template=params.template,
            output=params.output_pdf,
            filters=params.filters,
        )
        result = pipeline.aggregate_result(
            bundle.path,
            output_pdf,
            collection.warnings,
        )
    except ValueError as exc:  # noqa: PERF203
        print(exc, file=sys.stderr)
        return 1

    write_warnings(result.warnings)
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    raise SystemExit(main())
