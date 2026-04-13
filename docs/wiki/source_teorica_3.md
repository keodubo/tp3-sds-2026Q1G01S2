---
type: "source"
title: "Source: Teorica 3"
summary: "Lecture notes on event-driven molecular dynamics of rigid spheres, including initialization, collision-time prediction, and collision operators."
tags: ["source", "teorica", "event-driven", "rigid-spheres"]
source_path: "docs/raw/Teoricas/Teorica_3.pdf"
last_updated: "2026-04-13"
---
# Source: Teorica 3

**File**: [Teorica_3.pdf](../raw/Teoricas/Teorica_3.pdf)  
**Date Ingested**: 2026-04-13

## Summary
This is the strongest course-level theoretical source for the current implementation. It walks through event-driven molecular dynamics of rigid spheres, from overlap-free initialization to collision-time formulas and collision operators.

## Key Takeaways
- Event-driven simulation is preferable when dynamics are dominated by sparse, instantaneous collisions.
- Initialization should place particles one by one without overlap against existing particles or walls.
- The core loop is: predict next collision time, advance all particles, store state, apply the collision operator, repeat.
- Collision handling separates particle-particle resolution from boundary reflections.

## Impact on This Repo
- It directly informs [Concept: Event-Driven Simulation](event_driven_simulation.md).
- It directly informs [Concept: Hard-Sphere Collision Model](collision_model.md).
- It supports the initialization and output choices for [System 1: Scanning Rate](system_1_scanning_rate.md).

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Concept: Event-Driven Simulation](event_driven_simulation.md)
- [Concept: Hard-Sphere Collision Model](collision_model.md)
