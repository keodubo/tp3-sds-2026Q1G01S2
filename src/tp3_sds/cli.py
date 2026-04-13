from __future__ import annotations

import argparse
from pathlib import Path

from tp3_sds.paths import find_repo_root
from tp3_sds.system1.config import load_config, load_study_config, validate_config, validate_study_config
from tp3_sds.system1.delivery import build_delivery_package
from tp3_sds.system1.simulation import run_simulation
from tp3_sds.wiki import (
    append_log_entry,
    lint_wiki,
    refresh_index,
    scaffold_source,
    search_wiki,
    today,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tp3")
    parser.add_argument("--root", type=Path, default=None, help="Repository root. Defaults to auto-detected root.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    wiki_parser = subparsers.add_parser("wiki", help="Persistent wiki helpers.")
    wiki_subparsers = wiki_parser.add_subparsers(dest="wiki_command", required=True)

    wiki_search = wiki_subparsers.add_parser("search", help="Search the wiki index, then fall back to rg.")
    wiki_search.add_argument("query", nargs="+")

    wiki_scaffold = wiki_subparsers.add_parser("scaffold-source", help="Create or refresh a source stub.")
    wiki_scaffold.add_argument("raw_path", type=Path)

    wiki_subparsers.add_parser("refresh-index", help="Regenerate docs/wiki/index.md from page metadata.")
    wiki_subparsers.add_parser("lint", help="Run wiki integrity checks.")

    system1_parser = subparsers.add_parser("system1", help="System 1 hard-sphere tooling.")
    system1_subparsers = system1_parser.add_subparsers(dest="system1_command", required=True)

    validate_parser = system1_subparsers.add_parser("validate-config", help="Validate a System 1 TOML config.")
    validate_parser.add_argument("--config", required=True, type=Path)

    run_parser = system1_subparsers.add_parser("run", help="Run a System 1 simulation.")
    run_parser.add_argument("--config", required=True, type=Path)

    validate_study_parser = system1_subparsers.add_parser("validate-study", help="Validate a System 1 study TOML config.")
    validate_study_parser.add_argument("--config", required=True, type=Path)

    study_parser = system1_subparsers.add_parser("study", help="Run the System 1 study pipeline for points 1.1-1.4.")
    study_parser.add_argument("--config", required=True, type=Path)

    animate_parser = system1_subparsers.add_parser("animate", help="Render a GIF animation from a System 1 snapshot file.")
    animate_parser.add_argument("--input", required=True, type=Path)
    animate_parser.add_argument("--output", required=True, type=Path)
    animate_parser.add_argument("--fps", type=int, default=12)
    animate_parser.add_argument("--show-step-label", action="store_true")

    package_parser = system1_subparsers.add_parser("package-delivery", help="Build a compact System 1 delivery zip.")
    package_parser.add_argument("--output", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = find_repo_root(args.root)

    if args.command == "wiki":
        if args.wiki_command == "search":
            results = search_wiki(root, " ".join(args.query))
            if not results:
                print("No wiki matches found.")
                return 1
            for result in results:
                print(f"{result.source}: {result.title} -> {result.path.relative_to(root)}")
                print(f"  {result.snippet}")
            return 0

        if args.wiki_command == "scaffold-source":
            path = scaffold_source(root, args.raw_path)
            refresh_index(root)
            print(f"Scaffolded source page: {path.relative_to(root)}")
            return 0

        if args.wiki_command == "refresh-index":
            path = refresh_index(root)
            print(f"Refreshed {path.relative_to(root)}")
            return 0

        if args.wiki_command == "lint":
            issues = lint_wiki(root)
            if not issues:
                print("Wiki lint passed.")
                return 0
            for issue in issues:
                print(f"{issue.level.upper()} [{issue.code}] {issue.path.relative_to(root)}: {issue.message}")
            return 1

    if args.command == "system1":
        if args.system1_command == "validate-config":
            config_path = args.config.resolve()
            config = load_config(config_path)
            validation = validate_config(config)
            if validation.errors:
                print("Config validation failed:")
                for error in validation.errors:
                    print(f"- {error}")
                for warning in validation.warnings:
                    print(f"- warning: {warning}")
                return 1
            print("Config validation passed.")
            for warning in validation.warnings:
                print(f"- warning: {warning}")
            return 0

        if args.system1_command == "validate-study":
            config_path = args.config.resolve()
            config = load_study_config(config_path)
            validation = validate_study_config(config)
            if validation.errors:
                print("Study config validation failed:")
                for error in validation.errors:
                    print(f"- {error}")
                for warning in validation.warnings:
                    print(f"- warning: {warning}")
                return 1
            print("Study config validation passed.")
            for warning in validation.warnings:
                print(f"- warning: {warning}")
            return 0

        if args.system1_command == "run":
            config_path = args.config.resolve()
            config = load_config(config_path)
            validation = validate_config(config)
            if validation.errors:
                print("Config validation failed:")
                for error in validation.errors:
                    print(f"- {error}")
                return 1
            result = run_simulation(config, config_path=config_path)
            append_log_entry(
                root,
                f"## [{today()}] run | System 1 simulation",
                [
                    f"Executed `tp3 system1 run --config {config_path}`.",
                    f"Generated output: `{result.output_path}`.",
                    f"Processed events: {result.processed_events}.",
                ],
            )
            print(f"Wrote animator output to {result.output_path}")
            print(f"Processed events: {result.processed_events}")
            print(f"Snapshots written: {result.snapshots_written}")
            print(f"Scanning count: {result.scanning_count}")
            return 0

        if args.system1_command == "study":
            from tp3_sds.system1.study import run_study

            config_path = args.config.resolve()
            config = load_study_config(config_path)
            validation = validate_study_config(config)
            if validation.errors:
                print("Study config validation failed:")
                for error in validation.errors:
                    print(f"- {error}")
                return 1
            result = run_study(config, config_path=config_path)
            append_log_entry(
                root,
                f"## [{today()}] run | System 1 study",
                [
                    f"Executed `tp3 system1 study --config {config_path}`.",
                    f"Study root: `{result.study_root}`.",
                    f"Particle counts: {result.particle_counts}.",
                ],
            )
            print(f"Study root: {result.study_root}")
            print(f"Particle counts: {result.particle_counts}")
            print(f"Summary: {result.summary_path}")
            return 0

        if args.system1_command == "animate":
            from tp3_sds.system1.animation import render_snapshot_animation

            input_path = args.input.resolve()
            output_path = args.output.resolve()
            render_snapshot_animation(
                input_path=input_path,
                output_path=output_path,
                fps=args.fps,
                show_step_label=args.show_step_label,
            )
            print(f"Wrote animation to {output_path}")
            return 0

        if args.system1_command == "package-delivery":
            output_path = args.output.resolve()
            build_delivery_package(root, output_path)
            print(f"Built delivery package at {output_path}")
            return 0

    parser.print_help()
    return 1
