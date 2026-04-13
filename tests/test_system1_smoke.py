from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from tp3_sds.cli import main
from tp3_sds.system1.config import load_config, validate_config
from tp3_sds.system1.delivery import build_delivery_package
from tp3_sds.system1.output import parse_output
from tp3_sds.system1.simulation import has_any_overlap, run_simulation


def test_system1_smoke_run_generates_parseable_output(tmp_path: Path) -> None:
    config_path = tmp_path / "system1.toml"
    output_path = tmp_path / "artifacts" / "run.txt"
    config_path.write_text(
        "\n".join(
            [
                "[simulation]",
                "duration = 0.5",
                "seed = 7",
                "max_events = 100",
                "",
                "[geometry]",
                "diameter = 20.0",
                "obstacle_radius = 1.0",
                "particle_radius = 1.0",
                "",
                "[particles]",
                "count = 3",
                "mass = 1.0",
                "speed = 1.0",
                "",
                "[output]",
                f'path = "{output_path.as_posix()}"',
                "snapshot_every = 1",
                "fresh_color = [0, 255, 0]",
                "used_color = [148, 0, 211]",
                "",
                "[observables]",
                "radial_bin_width = 0.5",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)
    validation = validate_config(config)

    assert validation.is_valid, validation.errors

    result = run_simulation(config, config_path=config_path)
    steps = parse_output(output_path)

    assert output_path.exists()
    assert steps
    assert steps[0].time == 0.0
    assert [step.time for step in steps] == sorted(step.time for step in steps)
    assert steps[-1].time == result.final_time
    assert {"r", "g", "b"} <= set(steps[0].particles[0].keys())
    assert not has_any_overlap(result.final_particles)


def test_system1_study_and_package_smoke(tmp_path: Path) -> None:
    root_path = tmp_path / "repo-root"
    (root_path / "docs" / "wiki").mkdir(parents=True)
    (root_path / "CLAUDE.md").write_text("# test root\n", encoding="utf-8")

    study_config_path = tmp_path / "study.toml"
    study_config_path.write_text(
        "\n".join(
            [
                "[geometry]",
                "diameter = 20.0",
                "obstacle_radius = 1.0",
                "particle_radius = 1.0",
                "",
                "[particles]",
                "count = 2",
                "mass = 1.0",
                "speed = 1.0",
                "",
                "[observables]",
                "radial_bin_width = 0.5",
                "",
                "[study]",
                'study_id = "smoke-study"',
                'counts_mode = "explicit"',
                "counts = [2]",
                "repetitions = 1",
                "seed_start = 10",
                "runtime_duration = 0.5",
                "runtime_limit_seconds = 20.0",
                "snapshot_every = 1",
                "generate_figures = true",
                f'artifacts_root = "{(tmp_path / "artifacts").as_posix()}"',
                "max_events = 1000",
                "",
                "[analysis]",
                "resample_dt = 0.5",
                "window_seconds = 0.5",
                "check_interval = 0.5",
                "tolerance = 1.0",
                "consecutive_checks = 1",
                "settle_extension = 0.5",
                "max_time = 2.0",
            ]
        ),
        encoding="utf-8",
    )

    assert main(["--root", str(root_path), "system1", "validate-study", "--config", str(study_config_path)]) == 0
    assert main(["--root", str(root_path), "system1", "study", "--config", str(study_config_path)]) == 0

    study_root = tmp_path / "artifacts" / "smoke-study"
    assert (study_root / "summary.md").exists()
    assert (study_root / "aggregates" / "runtime_vs_n.csv").exists()
    assert (study_root / "aggregates" / "scanning_rate_vs_n.csv").exists()
    assert (study_root / "figures" / "runtime_vs_n.png").exists()

    package_path = tmp_path / "delivery.zip"
    build_delivery_package(Path.cwd(), package_path)
    assert package_path.exists()
    assert package_path.stat().st_size < 100_000
    with ZipFile(package_path) as archive:
        names = set(archive.namelist())
    assert "README.md" in names
    assert "src/tp3_sds/cli.py" in names
    assert "src/tp3_sds/system1/simulation.py" in names
