from __future__ import annotations

import math
from dataclasses import dataclass

from tp3_sds.system1.model import Geometry, Particle, ParticleState


@dataclass(frozen=True)
class RadialProfileBin:
    radius_start: float
    radius_end: float
    density: float
    normal_velocity: float
    inward_flux: float
    samples: int


class RadialProfileAccumulator:
    def __init__(self, geometry: Geometry, bin_width: float) -> None:
        self.geometry = geometry
        self.bin_width = bin_width
        span = geometry.outer_travel_radius - geometry.inner_travel_radius
        self.bin_count = max(1, math.ceil(span / bin_width))
        self.density_sums = [0.0 for _ in range(self.bin_count)]
        self.velocity_sums = [0.0 for _ in range(self.bin_count)]
        self.sample_counts = [0 for _ in range(self.bin_count)]

    def record(self, particles: list[Particle]) -> None:
        counts = [0 for _ in range(self.bin_count)]
        velocity_sums = [0.0 for _ in range(self.bin_count)]
        inner = self.geometry.inner_travel_radius
        outer = self.geometry.outer_travel_radius

        for particle in particles:
            if particle.state != ParticleState.FRESH:
                continue
            radius = particle.distance_to_origin()
            if radius < inner or radius > outer:
                continue
            radial_dot = particle.radial_velocity()
            if radial_dot >= 0:
                continue
            index = min(self.bin_count - 1, int((radius - inner) / self.bin_width))
            counts[index] += 1
            velocity_sums[index] += radial_dot / radius

        for index in range(self.bin_count):
            radius_start = inner + index * self.bin_width
            radius_end = min(outer, radius_start + self.bin_width)
            area = math.pi * (radius_end * radius_end - radius_start * radius_start)
            density = counts[index] / area if area > 0 else 0.0
            velocity = velocity_sums[index] / counts[index] if counts[index] else 0.0
            self.density_sums[index] += density
            self.velocity_sums[index] += velocity
            self.sample_counts[index] += 1

    def export(self) -> list[RadialProfileBin]:
        bins: list[RadialProfileBin] = []
        inner = self.geometry.inner_travel_radius
        outer = self.geometry.outer_travel_radius
        for index in range(self.bin_count):
            radius_start = inner + index * self.bin_width
            radius_end = min(outer, radius_start + self.bin_width)
            samples = self.sample_counts[index]
            density = self.density_sums[index] / samples if samples else 0.0
            velocity = self.velocity_sums[index] / samples if samples else 0.0
            bins.append(
                RadialProfileBin(
                    radius_start=radius_start,
                    radius_end=radius_end,
                    density=density,
                    normal_velocity=velocity,
                    inward_flux=density * abs(velocity),
                    samples=samples,
                )
            )
        return bins


class System1Observables:
    def __init__(self, geometry: Geometry, radial_bin_width: float) -> None:
        self.scanning_count = 0
        self.used_fraction_history: list[tuple[float, float]] = []
        self.radial_profiles = RadialProfileAccumulator(geometry, radial_bin_width)

    def note_center_contact(self, was_fresh: bool) -> None:
        if was_fresh:
            self.scanning_count += 1

    def record_snapshot(self, time: float, particles: list[Particle]) -> None:
        if particles:
            used_fraction = sum(p.state == ParticleState.USED for p in particles) / len(particles)
        else:
            used_fraction = 0.0
        self.used_fraction_history.append((time, used_fraction))
        self.radial_profiles.record(particles)
