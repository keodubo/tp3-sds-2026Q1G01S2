---
type: "system"
title: "System 1: Scanning Rate"
summary: "Event-driven hard-sphere dynamics in a circular enclosure with a fixed central obstacle and fresh/used state changes."
tags: ["system", "system1", "hard-spheres", "event-driven"]
sources: ["source_tp3_enunciado.md", "source_molecular_dynamics_simulation_of_hard_spheres.md", "source_teorica_3.md"]
last_updated: "2026-04-13"
---
# System 1: Scanning Rate

This is the code target for the repository. It combines classical event-driven hard-sphere dynamics with a domain-specific state transition: particles become `used` when they hit the central obstacle and recover to `fresh` when they hit the outer boundary.

## Geometry and Fixed Parameters
- Circular enclosure of diameter `L = 80 m`.
- Fixed circular obstacle at the center with radius `r0 = 1 m`.
- `N` particles of radius `r = 1 m`, mass `m = 1 kg`, and speed `v0 = 1 m/s`.
- Initial directions uniformly distributed in `[0, 2π)`.

## Dynamic Rules
- Particles move ballistically between collisions.
- Particle-particle and particle-boundary interactions are elastic in the current v1 engine.
- A `fresh` particle that touches the center obstacle becomes `used`.
- A `used` particle that touches the outer boundary becomes `fresh` again.

## Required Observables
- Execution time as a function of `N` for a fixed absolute simulation time `tf = 5 s`.
- Cumulative fresh-to-center contacts `C_fc(t)` and the derived scanning rate `J`.
- Time evolution of the used fraction `F_u(t) = N_u(t)/N` and the stationary value `F_est`.
- Radial profiles for fresh particles moving inward, as detailed in [Observable: System 1 Measurements](system_1_observables.md).

## Implementation Pointers
- The event-driven rationale is summarized in [Concept: Event-Driven Simulation](event_driven_simulation.md).
- Collision-time prediction and collision resolution are summarized in [Concept: Hard-Sphere Collision Model](collision_model.md).
- Queue scheduling and stale-event handling are summarized in [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md).
- The current output format expected from the simulation motor is fixed in [Analysis: Animation Output Contract](animation_output_contract.md).
- Scope and architecture choices for the current repository are documented in [Decision: V1 Foundation Scope](decision_v1_foundation_scope.md).

## Primary Sources
- [Source: TP3 Enunciado](source_tp3_enunciado.md)
- [Source: Molecular Dynamics Simulation of Hard Spheres](source_molecular_dynamics_simulation_of_hard_spheres.md)
- [Source: Teorica 3](source_teorica_3.md)
