"""Command-line interface for rendering Markdown trees to PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import IO, Mapping, Sequence

from . import pipeline
from .reporting import write_warnings


class ProgressReporter:
    """Управляет выводом прогресса и дублирует его в лог."""

    def __init__(self, verbose: bool, log_file: Path | None) -> None:
        self.verbose = verbose
        self.log_file = log_file
        self._log_handle: IO[str] | None = None

    def __enter__(self) -> "ProgressReporter":
        if self.log_file is not None:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = open(self.log_file, "a", encoding="utf-8")
        return self

    def __exit__(self, *_: object) -> None:
        if self._log_handle is not None:
            self._log_handle.close()

    def stage(self, message: str) -> None:
        line = f"[md2pdf] {message}"
        if self.verbose:
            print(line, file=sys.stderr, flush=True)
        if self._log_handle is not None:
            self._log_handle.write(line + "\n")
            self._log_handle.flush()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Markdown content into a PDF using project configuration.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/project.yml"),
        help="Path to the project configuration file (default: config/project.yml).",
    )
    parser.add_argument(
        "--md-dir",
        dest="md_dir_flag",
        type=Path,
        help="Explicit markdown directory (fallback when positional arg is absent).",
    )
    parser.add_argument(
        "md_dir",
        nargs="?",
        type=Path,
        help="Markdown directory to render (preferred over --md-dir).",
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
        "--log-file",
        type=Path,
        help="Write verbose output and Pandoc logs into a file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output (Pandoc still emits errors).",
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
        md_dir = args.md_dir or args.md_dir_flag
        if md_dir is None:
            raise ValueError("Provide markdown directory as first argument or --md-dir")

        if args.log_file:
            args.log_file.unlink(missing_ok=True)

        metadata_overrides = _parse_metadata(args.metadata)
        params = pipeline.prepare_params(
            md_dir=md_dir,
            config_path=args.config,
            style_override=args.style,
            output_override=args.output,
            metadata_overrides=metadata_overrides,
        )

        verbose = not args.quiet
        with ProgressReporter(verbose=verbose, log_file=args.log_file) as progress:
            progress.stage(f"Collecting markdown from {params.md_root}")
            collection = pipeline.collect_markdown(params.md_root)

            progress.stage(f"Building bundle -> {params.bundle_path}")
            bundle = pipeline.assemble_bundle(
                collection.order,
                params.bundle_path,
                metadata=params.metadata,
            )

            progress.stage(
                f"Rendering PDF to {params.output_pdf} (style: {params.style.name})"
            )
            output_pdf = pipeline.render_pdf(
                bundle.path,
                style=params.style,
                template=params.template,
                output=params.output_pdf,
                filters=params.filters,
                verbose=verbose,
                log_file=args.log_file,
            )
            progress.stage("Done")

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
