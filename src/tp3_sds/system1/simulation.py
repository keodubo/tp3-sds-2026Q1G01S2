from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tp3_sds.system1.config import SimulationConfig, validate_config
from tp3_sds.system1.events import Event, EventKind
from tp3_sds.system1.model import Geometry, Particle, ParticleState
from tp3_sds.system1.observables import RadialProfileBin, System1Observables
from tp3_sds.system1.output import SnapshotWriter

EPSILON = 1e-9


@dataclass(frozen=True)
class SimulationResult:
    output_path: Path
    processed_events: int
    snapshots_written: int
    final_time: float
    scanning_count: int
    used_fraction_history: list[tuple[float, float]]
    radial_profiles: list[RadialProfileBin]
    final_particles: list[Particle]


def run_simulation(config: SimulationConfig, config_path: Path | None = None) -> SimulationResult:
    validation = validate_config(config)
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))

    particles = generate_initial_particles(config)
    observables = System1Observables(config.geometry, config.observables.radial_bin_width)
    queue: list[Event] = []
    sequence = 0
    current_time = 0.0
    processed_events = 0
    snapshots_written = 0
    last_snapshot_time = -math.inf

    def next_sequence() -> int:
        nonlocal sequence
        sequence += 1
        return sequence

    def push_event(event: Event) -> None:
        heapq.heappush(queue, event)

    def schedule_particle_events(particle_index: int, now: float) -> None:
        particle = particles[particle_index]
        t_outer = predict_outer_wall_collision_time(particle, config.geometry)
        if math.isfinite(t_outer) and now + t_outer <= config.duration + EPSILON:
            push_event(
                Event(
                    time=now + t_outer,
                    sequence=next_sequence(),
                    kind=EventKind.OUTER_WALL,
                    particle_a=particle_index,
                    count_a=particle.collision_count,
                )
            )

        t_inner = predict_inner_obstacle_collision_time(particle, config.geometry)
        if math.isfinite(t_inner) and now + t_inner <= config.duration + EPSILON:
            push_event(
                Event(
                    time=now + t_inner,
                    sequence=next_sequence(),
                    kind=EventKind.INNER_OBSTACLE,
                    particle_a=particle_index,
                    count_a=particle.collision_count,
                )
            )

        for other_index, other in enumerate(particles):
            if other_index == particle_index:
                continue
            collision_time = predict_particle_collision_time(particle, other)
            if math.isfinite(collision_time) and now + collision_time <= config.duration + EPSILON:
                push_event(
                    Event(
                        time=now + collision_time,
                        sequence=next_sequence(),
                        kind=EventKind.PARTICLE,
                        particle_a=particle_index,
                        particle_b=other_index,
                        count_a=particle.collision_count,
                        count_b=other.collision_count,
                    )
                )

    for index in range(len(particles)):
        schedule_particle_events(index, current_time)
    push_event(Event(time=config.duration, sequence=next_sequence(), kind=EventKind.STOP))

    config.output.path.parent.mkdir(parents=True, exist_ok=True)
    with config.output.path.open("w", encoding="utf-8") as handle:
        writer = SnapshotWriter(handle, config, config_path=config_path)
        writer.write_header()
        observables.record_snapshot(0.0, particles)
        writer.write_step(0, 0.0, particles)
        snapshots_written += 1
        last_snapshot_time = 0.0

        while queue:
            event = heapq.heappop(queue)
            if event.time + EPSILON < current_time:
                continue
            if not event.is_valid(particles):
                continue

            advance_all(particles, event.time - current_time)
            current_time = event.time

            if event.kind == EventKind.STOP:
                if current_time > last_snapshot_time + EPSILON:
                    observables.record_snapshot(current_time, particles)
                    writer.write_step(processed_events, current_time, particles)
                    snapshots_written += 1
                break

            if processed_events >= config.max_events:
                raise RuntimeError("Maximum event budget reached before simulation stop event.")

            touched: set[int] = set()
            if event.kind == EventKind.PARTICLE:
                resolve_particle_collision(
                    particles[event.particle_a],
                    particles[event.particle_b],
                )
                touched.update({event.particle_a, event.particle_b})
            elif event.kind == EventKind.OUTER_WALL:
                handle_boundary_collision(
                    particles[event.particle_a],
                    EventKind.OUTER_WALL,
                    observables,
                )
                touched.add(event.particle_a)
            elif event.kind == EventKind.INNER_OBSTACLE:
                handle_boundary_collision(
                    particles[event.particle_a],
                    EventKind.INNER_OBSTACLE,
                    observables,
                )
                touched.add(event.particle_a)

            processed_events += 1
            for index in touched:
                schedule_particle_events(index, current_time)

            if processed_events % config.output.snapshot_every == 0:
                observables.record_snapshot(current_time, particles)
                writer.write_step(processed_events, current_time, particles)
                snapshots_written += 1
                last_snapshot_time = current_time

    return SimulationResult(
        output_path=config.output.path,
        processed_events=processed_events,
        snapshots_written=snapshots_written,
        final_time=current_time,
        scanning_count=observables.scanning_count,
        used_fraction_history=observables.used_fraction_history,
        radial_profiles=observables.radial_profiles.export(),
        final_particles=[clone_particle(particle) for particle in particles],
    )


def clone_particle(particle: Particle) -> Particle:
    return Particle(
        id=particle.id,
        x=particle.x,
        y=particle.y,
        vx=particle.vx,
        vy=particle.vy,
        radius=particle.radius,
        mass=particle.mass,
        state=particle.state,
        collision_count=particle.collision_count,
    )


def generate_initial_particles(config: SimulationConfig) -> list[Particle]:
    generator = random.Random(config.seed)
    particles: list[Particle] = []
    inner = config.geometry.inner_travel_radius
    outer = config.geometry.outer_travel_radius
    max_attempts = max(5000, config.particles.count * 3000)

    for particle_id in range(config.particles.count):
        for _ in range(max_attempts):
            radius = math.sqrt(generator.uniform(inner * inner, outer * outer))
            angle = generator.uniform(0.0, 2.0 * math.pi)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            if all(distance_between_xy(x, y, other.x, other.y) >= 2.0 * config.geometry.particle_radius - EPSILON for other in particles):
                velocity_angle = generator.uniform(0.0, 2.0 * math.pi)
                particles.append(
                    Particle(
                        id=particle_id,
                        x=x,
                        y=y,
                        vx=config.particles.speed * math.cos(velocity_angle),
                        vy=config.particles.speed * math.sin(velocity_angle),
                        radius=config.geometry.particle_radius,
                        mass=config.particles.mass,
                    )
                )
                break
        else:
            raise ValueError(
                "Unable to place particles without overlap. Lower particles.count or particle_radius."
            )
    return particles


def advance_all(particles: list[Particle], dt: float) -> None:
    if abs(dt) <= EPSILON:
        return
    for particle in particles:
        particle.advance(dt)


def predict_particle_collision_time(particle_a: Particle, particle_b: Particle) -> float:
    dx = particle_b.x - particle_a.x
    dy = particle_b.y - particle_a.y
    dvx = particle_b.vx - particle_a.vx
    dvy = particle_b.vy - particle_a.vy
    dvdr = dx * dvx + dy * dvy
    if dvdr >= 0:
        return math.inf
    dvdv = dvx * dvx + dvy * dvy
    if dvdv <= EPSILON:
        return math.inf
    sigma = particle_a.radius + particle_b.radius
    drdr = dx * dx + dy * dy
    discriminant = dvdr * dvdr - dvdv * (drdr - sigma * sigma)
    if discriminant < 0:
        return math.inf
    collision_time = -(dvdr + math.sqrt(discriminant)) / dvdv
    if collision_time <= EPSILON:
        return math.inf
    return collision_time


def predict_outer_wall_collision_time(particle: Particle, geometry: Geometry) -> float:
    return predict_circle_collision_time(particle, geometry.outer_travel_radius, mode="outer")


def predict_inner_obstacle_collision_time(particle: Particle, geometry: Geometry) -> float:
    return predict_circle_collision_time(particle, geometry.inner_travel_radius, mode="inner")


def predict_circle_collision_time(particle: Particle, target_radius: float, mode: str) -> float:
    a = particle.vx * particle.vx + particle.vy * particle.vy
    if a <= EPSILON:
        return math.inf
    b = 2.0 * (particle.x * particle.vx + particle.y * particle.vy)
    c = particle.x * particle.x + particle.y * particle.y - target_radius * target_radius
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return math.inf
    sqrt_discriminant = math.sqrt(discriminant)
    roots = sorted(((-b - sqrt_discriminant) / (2.0 * a), (-b + sqrt_discriminant) / (2.0 * a)))
    for root in roots:
        if root <= EPSILON:
            continue
        x = particle.x + particle.vx * root
        y = particle.y + particle.vy * root
        radial_velocity = x * particle.vx + y * particle.vy
        if mode == "outer" and radial_velocity > 0:
            return root
        if mode == "inner" and radial_velocity < 0:
            return root
    return math.inf


def resolve_particle_collision(particle_a: Particle, particle_b: Particle) -> None:
    dx = particle_b.x - particle_a.x
    dy = particle_b.y - particle_a.y
    distance = math.hypot(dx, dy)
    if distance <= EPSILON:
        raise ValueError("Particles overlap at collision resolution time.")
    dvx = particle_b.vx - particle_a.vx
    dvy = particle_b.vy - particle_a.vy
    dvdr = dx * dvx + dy * dvy
    impulse = 2.0 * particle_a.mass * particle_b.mass * dvdr / (
        (particle_a.mass + particle_b.mass) * distance
    )
    fx = impulse * dx / distance
    fy = impulse * dy / distance
    particle_a.vx += fx / particle_a.mass
    particle_a.vy += fy / particle_a.mass
    particle_b.vx -= fx / particle_b.mass
    particle_b.vy -= fy / particle_b.mass
    particle_a.collision_count += 1
    particle_b.collision_count += 1


def handle_boundary_collision(
    particle: Particle,
    kind: EventKind,
    observables: System1Observables,
) -> None:
    reflect_velocity(particle)
    was_fresh = particle.state == ParticleState.FRESH
    if kind == EventKind.INNER_OBSTACLE:
        observables.note_center_contact(was_fresh=was_fresh)
        particle.state = ParticleState.USED
    elif kind == EventKind.OUTER_WALL and particle.state == ParticleState.USED:
        particle.state = ParticleState.FRESH
    particle.collision_count += 1


def reflect_velocity(particle: Particle) -> None:
    distance = particle.distance_to_origin()
    if distance <= EPSILON:
        raise ValueError("Cannot reflect a particle located at the origin.")
    nx = particle.x / distance
    ny = particle.y / distance
    dot = particle.vx * nx + particle.vy * ny
    particle.vx -= 2.0 * dot * nx
    particle.vy -= 2.0 * dot * ny


def distance_between_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def has_any_overlap(particles: list[Particle]) -> bool:
    for index, particle in enumerate(particles):
        for other in particles[index + 1 :]:
            if distance_between_xy(particle.x, particle.y, other.x, other.y) < particle.radius + other.radius - 1e-6:
                return True
    return False
