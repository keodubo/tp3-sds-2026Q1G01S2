from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from tp3_sds.system1.config import OutputConfig, SimulationConfig
from tp3_sds.system1.model import Particle, ParticleState


@dataclass(frozen=True)
class ParsedStep:
    event_id: int
    time: float
    n_used: int
    particles: list[dict[str, object]]


def particle_color(particle: Particle, output_config: OutputConfig) -> tuple[int, int, int]:
    if particle.state == ParticleState.USED:
        return output_config.used_color
    return output_config.fresh_color


class SnapshotWriter:
    def __init__(self, handle: TextIO, config: SimulationConfig, config_path: Path | None = None) -> None:
        self.handle = handle
        self.config = config
        self.config_path = config_path

    def write_header(self) -> None:
        geometry = self.config.geometry
        self.handle.write("# tp3-sds system1 output\n")
        if self.config_path is not None:
            self.handle.write(f"config_path = {self.config_path}\n")
        self.handle.write(f"duration = {self.config.duration:.6f}\n")
        self.handle.write(f"particle_count = {self.config.particles.count}\n")
        self.handle.write(f"domain_diameter = {geometry.diameter:.6f}\n")
        self.handle.write(f"obstacle_radius = {geometry.obstacle_radius:.6f}\n")
        self.handle.write(f"particle_radius = {geometry.particle_radius:.6f}\n")
        self.handle.write(f"snapshot_every = {self.config.output.snapshot_every}\n")
        self.handle.write(f"fresh_color = {','.join(str(value) for value in self.config.output.fresh_color)}\n")
        self.handle.write(f"used_color = {','.join(str(value) for value in self.config.output.used_color)}\n")
        self.handle.write("---\n")

    def write_step(self, event_id: int, time: float, particles: list[Particle]) -> None:
        n_used = sum(particle.state == ParticleState.USED for particle in particles)
        self.handle.write(f"step event_id={event_id} time={time:.6f} n_used={n_used}\n")
        for particle in particles:
            red, green, blue = particle_color(particle, self.config.output)
            self.handle.write(
                "particle "
                f"id={particle.id} "
                f"x={particle.x:.6f} "
                f"y={particle.y:.6f} "
                f"vx={particle.vx:.6f} "
                f"vy={particle.vy:.6f} "
                f"state={particle.state.value} "
                f"r={red} "
                f"g={green} "
                f"b={blue}\n"
            )


def parse_output(path: Path) -> list[ParsedStep]:
    steps: list[ParsedStep] = []
    current: ParsedStep | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("step "):
            if current is not None:
                steps.append(current)
            parts = _parse_fields(line)
            current = ParsedStep(
                event_id=int(parts["event_id"]),
                time=float(parts["time"]),
                n_used=int(parts["n_used"]),
                particles=[],
            )
        elif line.startswith("particle ") and current is not None:
            parts = _parse_fields(line)
            current.particles.append(
                {
                    "id": int(parts["id"]),
                    "x": float(parts["x"]),
                    "y": float(parts["y"]),
                    "vx": float(parts["vx"]),
                    "vy": float(parts["vy"]),
                    "state": parts["state"],
                    "r": int(parts["r"]),
                    "g": int(parts["g"]),
                    "b": int(parts["b"]),
                }
            )
    if current is not None:
        steps.append(current)
    return steps


def _parse_fields(line: str) -> dict[str, str]:
    chunks = line.split()[1:]
    parsed: dict[str, str] = {}
    for chunk in chunks:
        key, value = chunk.split("=", maxsplit=1)
        parsed[key] = value
    return parsed
