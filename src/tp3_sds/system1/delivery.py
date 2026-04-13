from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


DELIVERY_CLI = """from __future__ import annotations

import argparse
from pathlib import Path

from tp3_sds.system1.config import load_config, validate_config
from tp3_sds.system1.simulation import run_simulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tp3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    system1_parser = subparsers.add_parser("system1")
    system1_subparsers = system1_parser.add_subparsers(dest="system1_command", required=True)

    validate_parser = system1_subparsers.add_parser("validate-config")
    validate_parser.add_argument("--config", required=True, type=Path)

    run_parser = system1_subparsers.add_parser("run")
    run_parser.add_argument("--config", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config.resolve())
    validation = validate_config(config)

    if args.system1_command == "validate-config":
        if validation.errors:
            print("Config validation failed:")
            for error in validation.errors:
                print(f"- {error}")
            return 1
        print("Config validation passed.")
        for warning in validation.warnings:
            print(f"- warning: {warning}")
        return 0

    if validation.errors:
        print("Config validation failed:")
        for error in validation.errors:
            print(f"- {error}")
        return 1
    result = run_simulation(config, config_path=args.config.resolve())
    print(f"Wrote animator output to {result.output_path}")
    print(f"Processed events: {result.processed_events}")
    print(f"Snapshots written: {result.snapshots_written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

DELIVERY_PYPROJECT = """[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "tp3-sds-system1"
version = "0.1.0"
requires-python = ">=3.11"

[project.scripts]
tp3 = "tp3_sds.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
"""

DELIVERY_README = """# TP3 SDS System 1 Motor

This package contains only the System 1 simulation motor and the minimal CLI required to validate a config or run a simulation.

## Commands

```bash
python3 -m pip install -e .
tp3 system1 validate-config --config configs/system1.example.toml
tp3 system1 run --config configs/system1.example.toml
```
"""

DELIVERY_ALLOWLIST = [
    "src/tp3_sds/__init__.py",
    "src/tp3_sds/system1/__init__.py",
    "src/tp3_sds/system1/analysis.py",
    "src/tp3_sds/system1/config.py",
    "src/tp3_sds/system1/events.py",
    "src/tp3_sds/system1/model.py",
    "src/tp3_sds/system1/observables.py",
    "src/tp3_sds/system1/output.py",
    "src/tp3_sds/system1/simulation.py",
]


def build_delivery_package(root: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("pyproject.toml", DELIVERY_PYPROJECT)
        archive.writestr("README.md", DELIVERY_README)
        archive.writestr("src/tp3_sds/__main__.py", "from tp3_sds.cli import main\n\nraise SystemExit(main())\n")
        archive.writestr("src/tp3_sds/cli.py", DELIVERY_CLI)
        for relative_path in DELIVERY_ALLOWLIST:
            archive.write(root / relative_path, arcname=relative_path)
        archive.write(root / "configs" / "system1.example.toml", arcname="configs/system1.example.toml")
    return output_path
