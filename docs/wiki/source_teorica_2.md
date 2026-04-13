---
type: "source"
title: "Source: Teorica 2"
summary: "Lecture notes on cellular automata, lattice gas models, and off-lattice agent systems; useful mainly as a modeling contrast."
tags: ["source", "teorica", "cellular-automata", "lattice-gas"]
source_path: "docs/raw/Teoricas/Teorica_2.pdf"
last_updated: "2026-04-13"
---
# Source: Teorica 2

**File**: [Teorica_2.pdf](../raw/Teoricas/Teorica_2.pdf)  
**Date Ingested**: 2026-04-13

## Summary
This lecture covers cellular automata, lattice gas models, and an off-lattice flocking example. It is less directly tied to the current implementation than [Source: Teorica 3](source_teorica_3.md), but it is still useful as a modeling contrast: not every simulation problem should be solved with the same state representation or temporal scheme.

## Key Takeaways
- Cellular automata use discrete states, local neighborhoods, and synchronous updates.
- Lattice gas models split evolution into propagation plus collision phases.
- Off-lattice examples show how continuous positions can coexist with simplified update rules.

## Impact on This Repo
- It helps clarify why `Sistema 1` is being implemented as continuous event-driven dynamics instead of a gridded time-step automaton.
- It supports presentation-level comparisons between modeling paradigms if needed later.

## Related Pages
- [Concept: Event-Driven Simulation](event_driven_simulation.md)
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [System 2: Smart Queues](system_2_smart_queues.md)
