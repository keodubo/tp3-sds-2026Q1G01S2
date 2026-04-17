from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from tp3_sds.cli import main
from tp3_sds.system1.animation import (
    AnimationFrame,
    InterpolatedParticle,
    build_animation_frames,
)
from tp3_sds.system1.output import (
    ParsedParticle,
    ParsedSnapshotOutput,
    ParsedStep,
    SnapshotHeader,
    parse_output,
    parse_snapshot_output,
)


def test_parse_snapshot_output_reads_header_and_steps(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "snapshot.txt"
    snapshot_path.write_text(_sample_snapshot_text(), encoding="utf-8")

    parsed = parse_snapshot_output(snapshot_path)
    steps = parse_output(snapshot_path)

    assert parsed.header.duration == 1.5
    assert parsed.header.particle_count == 2
    assert parsed.header.fresh_color == (0, 255, 0)
    assert len(parsed.steps) == 2
    assert len(steps) == 2
    assert parsed.steps[1].n_used == 1
    assert parsed.steps[1].particles[1].state == "used"
    assert (parsed.steps[1].particles[1].r, parsed.steps[1].particles[1].g, parsed.steps[1].particles[1].b) == (
        148,
        0,
        211,
    )


def test_parse_snapshot_output_rejects_missing_header_field(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "snapshot.txt"
    snapshot_path.write_text(_sample_snapshot_text().replace("obstacle_radius = 1.000000\n", ""), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required header fields"):
        parse_snapshot_output(snapshot_path)


def test_parse_snapshot_output_rejects_truncated_step(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "snapshot.txt"
    truncated = _sample_snapshot_text().replace(
        "particle id=1 x=-2.500000 y=0.000000 vx=1.000000 vy=0.000000 state=used r=148 g=0 b=211\n",
        "",
    )
    snapshot_path.write_text(truncated, encoding="utf-8")

    with pytest.raises(ValueError, match="expected 2"):
        parse_snapshot_output(snapshot_path)


def test_simulation_import_does_not_require_matplotlib(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    code = """
import builtins

original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "matplotlib" or name.startswith("matplotlib."):
        raise RuntimeError("unexpected matplotlib import")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
from tp3_sds.system1.simulation import run_simulation
print(run_simulation.__name__)
"""
    environment = os.environ.copy()
    pythonpath = str(repo_root / "src")
    if environment.get("PYTHONPATH"):
        pythonpath = os.pathsep.join([pythonpath, environment["PYTHONPATH"]])
    environment["PYTHONPATH"] = pythonpath

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "run_simulation"


def test_system1_animate_cli_writes_gif(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "snapshot.txt"
    output_path = tmp_path / "animation.gif"
    snapshot_path.write_text(_sample_snapshot_text(), encoding="utf-8")

    assert main(
        [
            "system1",
            "animate",
            "--input",
            str(snapshot_path),
            "--output",
            str(output_path),
            "--fps",
            "8",
            "--show-step-label",
        ]
    ) == 0

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def _sample_snapshot_text() -> str:
    return dedent(
        """\
        # tp3-sds system1 output
        config_path = configs/system1.example.toml
        duration = 1.500000
        particle_count = 2
        domain_diameter = 80.000000
        obstacle_radius = 1.000000
        particle_radius = 1.000000
        snapshot_every = 1
        fresh_color = 0,255,0
        used_color = 148,0,211
        ---
        step event_id=0 time=0.000000 n_used=0
        particle id=0 x=3.000000 y=0.000000 vx=-1.000000 vy=0.000000 state=fresh r=0 g=255 b=0
        particle id=1 x=-3.000000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0
        step event_id=1 time=0.500000 n_used=1
        particle id=0 x=2.500000 y=0.000000 vx=-1.000000 vy=0.000000 state=fresh r=0 g=255 b=0
        particle id=1 x=-2.500000 y=0.000000 vx=1.000000 vy=0.000000 state=used r=148 g=0 b=211
        """
    )


def _make_parsed(*, duration: float, steps: list[ParsedStep]) -> ParsedSnapshotOutput:
    header = SnapshotHeader(
        duration=duration,
        particle_count=len(steps[0].particles) if steps else 0,
        domain_diameter=80.0,
        obstacle_radius=1.0,
        particle_radius=1.0,
        snapshot_every=1,
        fresh_color=(0, 255, 0),
        used_color=(148, 0, 211),
    )
    return ParsedSnapshotOutput(header=header, steps=steps)


def _p(id_: int, x: float, y: float, vx: float, vy: float) -> ParsedParticle:
    return ParsedParticle(id=id_, x=x, y=y, vx=vx, vy=vy, state="fresh", r=0, g=255, b=0)


def test_build_animation_frames_linear_interpolation_exact() -> None:
    parsed = _make_parsed(
        duration=2.0,
        steps=[
            ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 1.0, 0.0)]),
            ParsedStep(event_id=1, time=2.0, n_used=0, particles=[_p(0, 2.0, 0.0, 1.0, 0.0)]),
        ],
    )
    frames = build_animation_frames(parsed=parsed, fps=1, playback_duration=2.0)
    assert len(frames) == 2
    assert frames[0].t_frame == 0.0
    assert frames[0].particles[0].x == 0.0
    assert frames[1].t_frame == 1.0
    assert frames[1].particles[0].x == 1.0
    assert frames[1].particles[0].y == 0.0


def test_build_animation_frames_snapshot_boundary_uses_right_anchor() -> None:
    parsed = _make_parsed(
        duration=2.0,
        steps=[
            ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 1.0, 0.0)]),
            ParsedStep(event_id=1, time=1.0, n_used=0, particles=[_p(0, 1.0, 0.0, 0.0, 1.0)]),
            ParsedStep(event_id=2, time=2.0, n_used=0, particles=[_p(0, 1.0, 1.0, 0.0, 1.0)]),
        ],
    )
    frames = build_animation_frames(parsed=parsed, fps=1, playback_duration=2.0)
    assert frames[1].t_frame == 1.0
    assert frames[1].particles[0].x == 1.0
    assert frames[1].particles[0].y == 0.0


def test_build_animation_frames_count_equals_fps_times_duration() -> None:
    parsed = _make_parsed(
        duration=5.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 0.0, 0.0)])],
    )
    frames = build_animation_frames(parsed=parsed, fps=10, playback_duration=2.0)
    assert len(frames) == 20


def test_build_animation_frames_clamps_past_last_snapshot() -> None:
    parsed = _make_parsed(
        duration=5.0,
        steps=[
            ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 1.0, 0.0)]),
            ParsedStep(event_id=1, time=3.0, n_used=0, particles=[_p(0, 3.0, 0.0, 1.0, 0.0)]),
        ],
    )
    frames = build_animation_frames(parsed=parsed, fps=1, playback_duration=5.0)
    assert len(frames) == 5
    assert frames[-1].t_frame == 3.0
    assert frames[-1].particles[0].x == 3.0


def test_build_animation_frames_preserves_colors_and_n_used() -> None:
    used_particle = ParsedParticle(id=0, x=0.0, y=0.0, vx=0.0, vy=0.0, state="used", r=148, g=0, b=211)
    parsed = _make_parsed(
        duration=1.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=1, particles=[used_particle])],
    )
    frames = build_animation_frames(parsed=parsed, fps=2, playback_duration=1.0)
    assert frames[0].n_used == 1
    assert (frames[0].particles[0].r, frames[0].particles[0].g, frames[0].particles[0].b) == (148, 0, 211)


def test_build_animation_frames_rejects_non_positive_fps() -> None:
    parsed = _make_parsed(
        duration=1.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 0.0, 0.0)])],
    )
    with pytest.raises(ValueError, match="fps"):
        build_animation_frames(parsed=parsed, fps=0, playback_duration=1.0)


def test_build_animation_frames_rejects_non_positive_playback_duration() -> None:
    parsed = _make_parsed(
        duration=1.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 0.0, 0.0)])],
    )
    with pytest.raises(ValueError, match="playback_duration"):
        build_animation_frames(parsed=parsed, fps=10, playback_duration=0.0)
