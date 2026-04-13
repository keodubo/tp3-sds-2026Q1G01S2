---
type: "concept"
title: "Concept: Hard-Sphere Collision Model"
summary: "Collision-time prediction and elastic collision rules for particles, the outer enclosure, and the central obstacle."
tags: ["concept", "system1", "hard-spheres", "physics"]
sources: ["source_molecular_dynamics_simulation_of_hard_spheres.md", "source_teorica_3.md", "source_tp3_enunciado.md"]
last_updated: "2026-04-13"
---
# Concept: Hard-Sphere Collision Model

`Sistema 1` is a hard-sphere problem with an annular free-flight region: particle centers evolve between an inner forbidden radius set by the fixed obstacle and an outer forbidden radius set by the enclosure wall.

## State Variables Per Particle
- Position `(x, y)`.
- Velocity `(vx, vy)`.
- Radius `r` and mass `m`.
- Discrete state `fresh` or `used`.

## Collision Types
- Particle-particle elastic collision.
- Particle-outer-boundary reflection.
- Particle-inner-obstacle reflection.

## Prediction Rules
- Particle-particle collision time comes from the standard quadratic condition where center distance reaches `ri + rj`.
- Circular-boundary collisions are found by solving `|r + vt| = R_target` and choosing the physically relevant positive root.
- The central obstacle is treated as a circular reflecting boundary for the particle center at radius `r0 + r`.

## Resolution Rules
- Particle-particle collisions conserve linear momentum and kinetic energy in the current elastic v1 engine.
- Boundary and obstacle collisions reflect the velocity over the local surface normal.
- State changes are domain-specific and layered on top of the collision itself: obstacle contact can trigger `fresh -> used`; outer-boundary contact can trigger `used -> fresh`.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Concept: Event-Driven Simulation](event_driven_simulation.md)
- [Source: Molecular Dynamics Simulation of Hard Spheres](source_molecular_dynamics_simulation_of_hard_spheres.md)
- [Source: Teorica 3](source_teorica_3.md)
