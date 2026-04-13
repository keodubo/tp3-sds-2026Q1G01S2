---
type: "concept"
title: "Concept: Event-Driven Simulation"
summary: "Simulation scheme where state updates occur only when a discrete event happens."
tags: ["concept", "simulation", "system1", "system2"]
sources: ["source_tp3_enunciado.md", "source_teorica_3.md", "source_molecular_dynamics_simulation_of_hard_spheres.md"]
last_updated: "2026-04-13"
---
# Concept: Event-Driven Simulation

Event-driven simulation updates the system only when a relevant event occurs. For this TP, that is the right abstraction because both proposed systems evolve through sparse state changes rather than through a mandatory fixed `dt`.

## Why It Fits This Repo
- In [System 1: Scanning Rate](system_1_scanning_rate.md), events are collisions between particles, the outer boundary, and the central obstacle.
- In [System 2: Smart Queues](system_2_smart_queues.md), events are arrivals, service completions, and queue-advance moves.
- The [TP3 Enunciado](source_tp3_enunciado.md) explicitly asks to record system state on event times, or every integer number of events.

## Canonical Loop
1. Predict the next event time from the current state.
2. Advance the whole system to that time.
3. Save the state if the output policy requires it.
4. Apply the event operator only to the involved entities.
5. Recompute future events affected by that local change.

## Implementation Notes for System 1
- The concrete collision formulas and state updates are summarized in [Concept: Hard-Sphere Collision Model](collision_model.md).
- The scalable scheduling strategy is documented in [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md).
- The current Python foundation uses an event queue plus lazy invalidation, directly aligned with [Source: Molecular Dynamics Simulation of Hard Spheres](source_molecular_dynamics_simulation_of_hard_spheres.md) and [Source: Teorica 3](source_teorica_3.md).

## Limits of Validity
- The approach assumes effectively instantaneous collisions.
- It is most natural at low to moderate densities, where free-flight intervals remain meaningful.
- Multi-particle simultaneous collisions are not modeled explicitly in the current v1 foundation.
