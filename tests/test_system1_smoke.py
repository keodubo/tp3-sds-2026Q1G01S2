from __future__ import annotations

from pathlib import Path

from tp3_sds.system1.config import load_config, validate_config
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
    assert not has_any_overlap(result.final_particles)
