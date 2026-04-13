from __future__ import annotations

import argparse
from pathlib import Path

from tp3_sds.paths import find_repo_root
from tp3_sds.system1 import load_config, run_simulation, validate_config
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
        config_path = args.config.resolve()
        config = load_config(config_path)
        validation = validate_config(config)

        if args.system1_command == "validate-config":
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

        if args.system1_command == "run":
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

    parser.print_help()
    return 1
