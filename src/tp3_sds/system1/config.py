from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

from tp3_sds.system1.model import Geometry


@dataclass(frozen=True)
class ParticleConfig:
    count: int
    mass: float = 1.0
    speed: float = 1.0


@dataclass(frozen=True)
class OutputConfig:
    path: Path
    snapshot_every: int = 1


@dataclass(frozen=True)
class ObservableConfig:
    radial_bin_width: float = 0.2


@dataclass(frozen=True)
class SimulationConfig:
    geometry: Geometry
    particles: ParticleConfig
    output: OutputConfig
    observables: ObservableConfig
    duration: float
    seed: int | None = None
    max_events: int = 100_000


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def load_config(path: Path) -> SimulationConfig:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    simulation = data.get("simulation", {})
    geometry_data = data.get("geometry", {})
    particles_data = data.get("particles", {})
    output_data = data.get("output", {})
    observables_data = data.get("observables", {})

    geometry = Geometry(
        diameter=float(geometry_data.get("diameter", 80.0)),
        obstacle_radius=float(geometry_data.get("obstacle_radius", 1.0)),
        particle_radius=float(geometry_data.get("particle_radius", 1.0)),
    )
    particles = ParticleConfig(
        count=int(particles_data.get("count", 0)),
        mass=float(particles_data.get("mass", 1.0)),
        speed=float(particles_data.get("speed", 1.0)),
    )
    output_path = Path(output_data.get("path", "artifacts/system1/latest.txt"))
    if not output_path.is_absolute():
        output_path = (path.parent / output_path).resolve()
    output = OutputConfig(
        path=output_path,
        snapshot_every=int(output_data.get("snapshot_every", 1)),
    )
    observables = ObservableConfig(
        radial_bin_width=float(observables_data.get("radial_bin_width", 0.2))
    )
    return SimulationConfig(
        geometry=geometry,
        particles=particles,
        output=output,
        observables=observables,
        duration=float(simulation.get("duration", 5.0)),
        seed=int(simulation["seed"]) if "seed" in simulation else None,
        max_events=int(simulation.get("max_events", 100_000)),
    )


def validate_config(config: SimulationConfig) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if config.duration <= 0:
        errors.append("simulation.duration must be positive.")
    if config.max_events <= 0:
        errors.append("simulation.max_events must be positive.")
    if config.particles.count <= 0:
        errors.append("particles.count must be greater than zero.")
    if config.particles.mass <= 0:
        errors.append("particles.mass must be positive.")
    if config.particles.speed <= 0:
        errors.append("particles.speed must be positive.")
    if config.output.snapshot_every <= 0:
        errors.append("output.snapshot_every must be greater than zero.")
    if config.observables.radial_bin_width <= 0:
        errors.append("observables.radial_bin_width must be positive.")

    geometry = config.geometry
    if geometry.diameter <= 0:
        errors.append("geometry.diameter must be positive.")
    if geometry.obstacle_radius <= 0:
        errors.append("geometry.obstacle_radius must be positive.")
    if geometry.particle_radius <= 0:
        errors.append("geometry.particle_radius must be positive.")
    if geometry.outer_travel_radius <= geometry.inner_travel_radius:
        errors.append("The annulus available to particle centers must have positive width.")

    annulus_area = math.pi * (
        geometry.outer_travel_radius * geometry.outer_travel_radius
        - geometry.inner_travel_radius * geometry.inner_travel_radius
    )
    particle_area = math.pi * geometry.particle_radius * geometry.particle_radius
    if annulus_area <= 0:
        errors.append("Available annulus area is non-positive.")
    elif config.particles.count * particle_area > annulus_area * 0.45:
        warnings.append(
            "Requested particle count occupies more than 45% of the annulus area; random placement may fail."
        )

    return ValidationResult(errors=errors, warnings=warnings)
