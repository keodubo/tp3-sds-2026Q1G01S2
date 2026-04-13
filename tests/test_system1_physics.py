from __future__ import annotations

import io
import math
from pathlib import Path

from tp3_sds.system1.config import ObservableConfig, OutputConfig, ParticleConfig, SimulationConfig
from tp3_sds.system1.events import Event, EventKind
from tp3_sds.system1.model import Geometry, Particle, ParticleState
from tp3_sds.system1.observables import RadialProfileAccumulator, System1Observables
from tp3_sds.system1.output import SnapshotWriter
from tp3_sds.system1.simulation import (
    handle_boundary_collision,
    predict_inner_obstacle_collision_time,
    predict_outer_wall_collision_time,
    predict_particle_collision_time,
    resolve_particle_collision,
)


def make_config(output_path: Path) -> SimulationConfig:
    return SimulationConfig(
        geometry=Geometry(diameter=10.0, obstacle_radius=1.0, particle_radius=0.5),
        particles=ParticleConfig(count=2, mass=1.0, speed=1.0),
        output=OutputConfig(path=output_path, snapshot_every=1),
        observables=ObservableConfig(radial_bin_width=1.0),
        duration=1.0,
        seed=1,
        max_events=100,
    )


def test_particle_collision_time() -> None:
    particle_a = Particle(id=0, x=-2.0, y=0.0, vx=1.0, vy=0.0, radius=0.5, mass=1.0)
    particle_b = Particle(id=1, x=2.0, y=0.0, vx=-1.0, vy=0.0, radius=0.5, mass=1.0)

    collision_time = predict_particle_collision_time(particle_a, particle_b)

    assert math.isclose(collision_time, 1.5, rel_tol=1e-9)


def test_outer_and_inner_wall_collision_time() -> None:
    geometry = Geometry(diameter=10.0, obstacle_radius=1.0, particle_radius=0.5)
    outer_particle = Particle(id=0, x=0.0, y=2.0, vx=0.0, vy=1.0, radius=0.5, mass=1.0)
    inner_particle = Particle(id=1, x=3.0, y=0.0, vx=-1.0, vy=0.0, radius=0.5, mass=1.0)

    assert math.isclose(predict_outer_wall_collision_time(outer_particle, geometry), 2.5, rel_tol=1e-9)
    assert math.isclose(predict_inner_obstacle_collision_time(inner_particle, geometry), 1.5, rel_tol=1e-9)


def test_particle_collision_response_conserves_velocity_exchange() -> None:
    particle_a = Particle(id=0, x=-0.5, y=0.0, vx=1.0, vy=0.0, radius=0.5, mass=1.0)
    particle_b = Particle(id=1, x=0.5, y=0.0, vx=-1.0, vy=0.0, radius=0.5, mass=1.0)

    resolve_particle_collision(particle_a, particle_b)

    assert math.isclose(particle_a.vx, -1.0, rel_tol=1e-9)
    assert math.isclose(particle_b.vx, 1.0, rel_tol=1e-9)
    assert particle_a.collision_count == 1
    assert particle_b.collision_count == 1


def test_stale_event_invalidation() -> None:
    particle = Particle(id=0, x=2.0, y=0.0, vx=-1.0, vy=0.0, radius=0.5, mass=1.0)
    event = Event(
        time=1.0,
        sequence=1,
        kind=EventKind.INNER_OBSTACLE,
        particle_a=0,
        count_a=0,
    )

    assert event.is_valid([particle])
    particle.collision_count += 1
    assert not event.is_valid([particle])


def test_boundary_collision_updates_state_and_scanning_count(tmp_path: Path) -> None:
    config = make_config(tmp_path / "output.txt")
    observables = System1Observables(config.geometry, radial_bin_width=1.0)
    particle = Particle(id=0, x=1.5, y=0.0, vx=-1.0, vy=0.0, radius=0.5, mass=1.0)

    handle_boundary_collision(particle, EventKind.INNER_OBSTACLE, observables)
    assert particle.state == ParticleState.USED
    assert observables.scanning_count == 1

    handle_boundary_collision(particle, EventKind.OUTER_WALL, observables)
    assert particle.state == ParticleState.FRESH


def test_radial_profile_binning() -> None:
    geometry = Geometry(diameter=10.0, obstacle_radius=1.0, particle_radius=0.5)
    accumulator = RadialProfileAccumulator(geometry, bin_width=1.0)
    particles = [
        Particle(id=0, x=2.0, y=0.0, vx=-1.0, vy=0.0, radius=0.5, mass=1.0, state=ParticleState.FRESH),
        Particle(id=1, x=4.0, y=0.0, vx=1.0, vy=0.0, radius=0.5, mass=1.0, state=ParticleState.FRESH),
    ]

    accumulator.record(particles)
    exported = accumulator.export()

    first_bin = exported[0]
    assert first_bin.samples == 1
    assert first_bin.density > 0
    assert first_bin.normal_velocity < 0
    assert first_bin.inward_flux > 0


def test_snapshot_serialization(tmp_path: Path) -> None:
    buffer = io.StringIO()
    config = make_config(tmp_path / "output.txt")
    writer = SnapshotWriter(buffer, config)
    particles = [
        Particle(id=0, x=1.0, y=2.0, vx=0.5, vy=-0.5, radius=0.5, mass=1.0),
    ]

    writer.write_header()
    writer.write_step(3, 1.25, particles)
    text = buffer.getvalue()

    assert "# tp3-sds system1 output" in text
    assert "step event_id=3 time=1.250000 n_used=0" in text
    assert "particle id=0 x=1.000000 y=2.000000 vx=0.500000 vy=-0.500000 state=fresh" in text
