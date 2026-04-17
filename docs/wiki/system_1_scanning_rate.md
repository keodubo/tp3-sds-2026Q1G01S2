---
type: "system"
title: "System 1: Scanning Rate"
summary: "Hard-sphere event-driven dynamics in a circular enclosure, with stateful particles, explicit color output, and a study pipeline for TP3 points 1.1-1.4."
tags: ["system", "system1", "hard-spheres", "event-driven"]
sources: ["source_tp3_enunciado.md", "source_molecular_dynamics_simulation_of_hard_spheres.md", "source_teorica_3.md"]
last_updated: "2026-04-17"
---
# System 1: Scanning Rate

This is the execution target of the repository. It combines classical event-driven hard-sphere dynamics with a domain-specific state transition and a TP-specific measurement protocol.

## Physical Model
- Circular enclosure of diameter `L = 80 m`.
- Fixed central obstacle of radius `r0 = 1 m`.
- Particle radius `r = 1 m`, mass `m = 1 kg`, speed `v0 = 1 m/s`.
- Initial directions uniformly sampled in `[0, 2π)`.
- Particles move ballistically between events.

## State Machine
- `fresh` state:
  - initial particle state
  - represented in the simulator output as green `(0,255,0)`
- `used` state:
  - reached after a fresh particle touches the central obstacle
  - represented in the simulator output as violet `(148,0,211)`
- `used -> fresh` transition:
  - triggered when a used particle touches the outer boundary

## Event Types
- particle-particle collision
- particle-outer-boundary collision
- particle-inner-obstacle collision

## What the Code Must Deliver
- A single-run motor exposed by `tp3 system1 run`.
- A study pipeline exposed by `tp3 system1 study` that covers:
  - `1.1` runtime vs `N`
  - `1.2` scanning rate `J`
  - `1.3` stationary used fraction `F_est` and stationary time
  - `1.4` radial profiles and near-shell metrics
- A compact delivery package exposed by `tp3 system1 package-delivery`.
- The original repository-level scope choice that prioritized System 1 and Python is documented in [Decision: V1 Foundation Scope](decision_v1_foundation_scope.md).

## Output Requirements
- The simulator output must include positions, velocities, state, and explicit RGB color per particle.
- The output is plain text and intended for an external animation module.
- The output contract is fixed in [Analysis: Animation Output Contract](animation_output_contract.md).

## Experimental Protocol
- Multiple realizations are required for each `N`.
- Runtime is measured separately at fixed `tf = 500 s` (see [errata](source_tp3_enunciado.md#errata-cátedra)).
- Observables `1.2–1.4` use an adaptive stationary protocol documented in [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md).
- Radial shells use `dS = 0.2 m`.
- The near-shell convention for the TP-specific `S ≈ 2` analysis is `[2.0, 2.2)`.

## Related Pages
- [Concept: Event-Driven Simulation](event_driven_simulation.md)
- [Concept: Hard-Sphere Collision Model](collision_model.md)
- [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md)
- [Observable: System 1 Measurements](system_1_observables.md)
- [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md)
- [Analysis: Animation Output Contract](animation_output_contract.md)
- [Decision: V1 Foundation Scope](decision_v1_foundation_scope.md)
