---
type: "analysis"
title: "Analysis: Animation Output Contract"
summary: "Plain-text output contract for System 1, now including explicit RGB color per particle to satisfy the TP statement."
tags: ["analysis", "system1", "output", "animation"]
sources: ["source_tp3_enunciado.md", "source_guia_presentaciones.md"]
last_updated: "2026-04-13"
---
# Analysis: Animation Output Contract

The assignment explicitly asks the simulation motor to print particle positions, velocities, and color. The repository therefore treats RGB color as part of the simulation output, not as implicit UI logic.

## Current File Shape
- Header metadata:
  - config path
  - duration
  - particle count
  - domain diameter
  - obstacle radius
  - particle radius
  - snapshot cadence
  - fresh color
  - used color
- Repeated `step` entries:
  - `event_id`
  - `time`
  - `n_used`
- Repeated `particle` entries:
  - `id`
  - `x`
  - `y`
  - `vx`
  - `vy`
  - `state`
  - `r`
  - `g`
  - `b`

## Default Color Mapping
- `fresh = (0,255,0)`
- `used = (148,0,211)`

## Why This Contract Exists
- It is directly aligned with the wording of [Source: TP3 Enunciado](source_tp3_enunciado.md).
- It decouples the simulator from any future animation renderer.
- It makes the output self-describing enough for debugging and presentation asset generation.

## What Is Not Emitted Per Step
- The outer boundary and the central obstacle are not encoded as pseudo-particles.
- Geometry stays in header metadata because it is static for the entire run.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Observable: System 1 Measurements](system_1_observables.md)
- [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md)
