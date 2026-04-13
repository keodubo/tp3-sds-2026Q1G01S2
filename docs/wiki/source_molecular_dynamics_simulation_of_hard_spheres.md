---
type: "source"
title: "Source: Molecular Dynamics Simulation of Hard Spheres"
summary: "Reference note on event-driven hard-disc simulation, collision prediction, collision resolution, and lazy invalidation."
tags: ["source", "hard-spheres", "event-driven", "reference"]
source_path: "docs/raw/bibliografia/Molecular Dynamics Simulation of Hard Spheres.pdf"
last_updated: "2026-04-13"
---
# Source: Molecular Dynamics Simulation of Hard Spheres

**File**: [Molecular Dynamics Simulation of Hard Spheres.pdf](../raw/bibliografia/Molecular%20Dynamics%20Simulation%20of%20Hard%20Spheres.pdf)  
**Date Ingested**: 2026-04-13  
**Origin**: COS 226 programming assignment and technical note

## Summary
This source is the most directly reusable implementation reference for the current repository. It describes event-driven hard-disc simulation, prioritizes collision-time prediction over fixed-`dt` stepping, and recommends a lazy invalidation strategy for stale events in the event queue.

## Key Takeaways
- Hard spheres move at constant velocity between collisions.
- Event-driven simulation is more robust and efficient than time-driven stepping for this class of systems.
- The core data structures are particles, events, and a priority queue of future collisions.
- Collision prediction for both walls and particle pairs reduces to closed-form formulas.
- After each real collision, only the future involving touched particles must be rescheduled.

## What Transfers Cleanly to TP3
- The queue strategy documented in [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md).
- The collision formulas summarized in [Concept: Hard-Sphere Collision Model](collision_model.md).
- The separation between simulation motor and visualization layer, which aligns with [Analysis: Animation Output Contract](animation_output_contract.md).

## What Needs Adaptation
- The reference uses a unit box with horizontal and vertical walls, while TP3 uses a circular enclosure plus a fixed circular obstacle.
- TP3 adds a particle state machine (`fresh`/`used`) on top of the collision dynamics.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Concept: Hard-Sphere Collision Model](collision_model.md)
- [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md)
