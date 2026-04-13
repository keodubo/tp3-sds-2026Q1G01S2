---
type: "concept"
title: "Concept: Event Queue and Lazy Invalidation"
summary: "Priority-queue scheduling strategy where stale events remain queued and are discarded when popped."
tags: ["concept", "system1", "queue", "algorithm"]
sources: ["source_molecular_dynamics_simulation_of_hard_spheres.md", "source_teorica_3.md"]
last_updated: "2026-04-13"
---
# Concept: Event Queue and Lazy Invalidation

The implementation strategy for [System 1: Scanning Rate](system_1_scanning_rate.md) uses a priority queue of future events. This follows the hard-sphere reference model closely and avoids recomputing the entire future after every collision.

## Core Idea
- Each queued event stores the predicted event time and the collision counters of the involved particles.
- If any involved particle has collided since the event was scheduled, the event is stale.
- Stale events are not proactively removed from the heap; they are dropped when they reach the top.

## Why This Matters
- It keeps the event queue simple.
- It localizes recomputation to the particles affected by the last processed event.
- It is a clean fit for the current Python foundation, where clarity matters more than extreme optimization.

## What Gets Rescheduled
- Boundary events for each touched particle.
- Inner-obstacle events for each touched particle.
- Particle-particle events between each touched particle and every other particle.

## Related Pages
- [Concept: Event-Driven Simulation](event_driven_simulation.md)
- [Concept: Hard-Sphere Collision Model](collision_model.md)
- [Source: Molecular Dynamics Simulation of Hard Spheres](source_molecular_dynamics_simulation_of_hard_spheres.md)
- [Source: Teorica 3](source_teorica_3.md)
