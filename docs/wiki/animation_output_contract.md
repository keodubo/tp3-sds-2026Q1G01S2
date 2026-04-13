---
type: "analysis"
title: "Analysis: Animation Output Contract"
summary: "Repository decision for the text format emitted by the System 1 simulation motor."
tags: ["analysis", "system1", "output", "animation"]
sources: ["source_tp3_enunciado.md", "source_guia_presentaciones.md"]
last_updated: "2026-04-13"
---
# Analysis: Animation Output Contract

The TP requires the simulation motor to emit a text file that an external animation module can replay independently. The current repository fixes a minimal stable contract now so the engine and the animator remain decoupled.

## Current File Shape
- Header with metadata:
  - duration
  - particle count
  - domain diameter
  - obstacle radius
  - particle radius
  - snapshot cadence
- Repeated `step` entries:
  - `event_id`
  - `time`
  - `n_used`
- Repeated `particle` lines per step:
  - `id`
  - `x`
  - `y`
  - `vx`
  - `vy`
  - `state`

## Design Rationale
- The outer boundary and the obstacle are fixed geometry, so they stay in metadata instead of being emitted as pseudo-particles.
- Recording by event count matches the assignment wording and fits [Concept: Event-Driven Simulation](event_driven_simulation.md).
- The contract stays plain text and parseable without requiring any binary tooling.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Decision: V1 Foundation Scope](decision_v1_foundation_scope.md)
- [Source: TP3 Enunciado](source_tp3_enunciado.md)
