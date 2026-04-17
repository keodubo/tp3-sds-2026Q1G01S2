---
type: "source"
title: "Source: TP3 Enunciado"
summary: "Detailed assignment source covering deliverables, System 1 physics, required studies 1.1-1.4, and constraints on the final code package."
tags: ["source", "tp3", "requirements", "system1"]
source_path: "docs/raw/TP3_Enunciado.pdf"
last_updated: "2026-04-17"
---
# Source: TP3 Enunciado

**File**: [TP3_Enunciado.pdf](../raw/TP3_Enunciado.pdf)  
**Date Ingested**: 2026-04-13  
**Subject**: Simulación Dirigida por Eventos (SDS - TP3)

## Executive Summary
This document is the authoritative contract for the repository. It does not just request an event-driven simulator: it also fixes what must be measured, what must be delivered, and how the simulation motor should relate to animation and presentation artifacts. For this repository, the relevant branch is [System 1: Scanning Rate](system_1_scanning_rate.md), which must be implemented as hard-sphere event-driven dynamics in a circular enclosure with a fixed central obstacle.

## Global Deliverables and Constraints

### Deliverables
- An oral presentation of `13` minutes.
- A PDF version of the presentation.
- A zip file containing only the final simulation motor source code.

### Naming and Submission Constraints
- Delivery deadline stated in the source: `2026-04-24 10:00`.
- Presentation and code must be uploaded through Campus.
- Required naming pattern:
  - `SdS_TP3_2026Q1GXXCSS_Presentación`
  - `SdS_TP3_2026Q1GXXCSS_Codigo`

### Code-Package Restrictions
- The final zip must be smaller than `100 KB`.
- It must include only the simulation motor.
- It must exclude:
  - previous versions
  - post-processing code
  - outputs
  - figures
  - results
  - extra documentation

### Animation Contract Required by the Statement
- The simulation motor must emit plain-text output.
- The animation module runs independently from that output.
- Animation speed must not depend on simulation speed.
- For System 1, the statement explicitly asks to print:
  - positions
  - velocities
  - particle color
- The repository therefore treats color as part of the simulator output contract, not as a downstream visualization-only concern. See [Analysis: Animation Output Contract](animation_output_contract.md).

## System 1: Physical Setup
- Circular enclosure diameter: `L = 80 m`.
- Fixed central circular obstacle radius: `r0 = 1 m`.
- Particle radius: `r = 1 m`.
- Particle mass: `m = 1 kg`.
- Particle speed magnitude: `v0 = 1 m/s`.
- Initial direction angles: uniform in `[0, 2π)`.
- The maximum `N` is not given explicitly; it must be chosen so simulations still complete in reasonable time.

## System 1: Dynamic Rules
- Motion is piecewise ballistic: particles move in straight lines with constant velocity between collisions.
- Time is intrinsically variable and determined by events.
- The simulation state should be recorded on event times, or every integer number of events.
- State machine:
  - all particles start `fresh` and should be visualized in green
  - a fresh particle becomes `used` after contacting the central obstacle
  - a used particle becomes `fresh` again after contacting the outer boundary

## System 1: Required Study 1.1
### Statement Requirement
- Simulate for fixed absolute time `tf = 5 s`.
- Vary `N`.
- Plot execution time as a function of `N`.

### Errata (cátedra)
- La cátedra confirmó oralmente que `tf = 5 s` es una errata del PDF.
- El valor correcto usado en este repositorio y aplicado a las simulaciones 1.1 a 1.4 es `tf = 500 s`.
- Esta página conserva la cita literal del PDF como referencia histórica; las páginas derivadas ([protocol](system_1_experimental_protocol.md), [observables](system_1_observables.md), [scanning rate](system_1_scanning_rate.md)) trabajan con el valor corregido.

### Implementation Implication
- The runtime study must time the real simulation motor, including snapshot generation, not just pure collision stepping.
- A study pipeline must support multiple `N` values and repeat runs to reduce timing noise.
- The repository standardizes this as part of `tp3 system1 study`.

## System 1: Required Study 1.2
### Statement Requirement
- Run multiple realizations for each `N`.
- Measure `C_fc(t)`: cumulative number of fresh particles that touched the center and changed state.
- Fit a line to `C_fc(t)`.
- Use the slope as the scanning rate `J`.
- Report averages and standard deviations of `J` over realizations.

### Implementation Implication
- The motor must preserve every `fresh -> used` center-contact event as a time series, not just a total count.
- The analysis layer must include:
  - time-resolved `C_fc(t)`
  - linear fitting in physical time
  - aggregation by `N`
  - error bars across realizations

## System 1: Required Study 1.3
### Statement Requirement
- Use the same realizations as in `1.2`.
- Study the time evolution of `F_u(t) = N_u(t)/N`.
- Report:
  - the time to stationary regime
  - the stationary value `F_est`
  - both as functions of `N`

### Implementation Implication
- The simulator must persist a time series of used-fraction snapshots.
- The study layer must define a stationary-detection protocol, because the statement asks for stationary metrics but does not define the detection rule.
- This repository adopts the protocol documented in [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md):
  - resample `F_u(t)` on a uniform time grid
  - compare consecutive windows
  - require repeated agreement before declaring stationarity
  - extend the run after detection to measure `F_est`

## System 1: Required Study 1.4
### Statement Requirement
- Use concentric shells of width `dS = 0.2 m`.
- Let `S` measure distance from the center.
- Restrict to fresh particles whose radial velocity points inward, meaning `R · v < 0`.
- Compute:
  - `⟨ρ_f^in⟩(S)`
  - `⟨v_f^in⟩(S)` with `v_f^in = (R · v)/|R|`
  - `J_in(S) = ⟨ρ_f^in⟩(S) |⟨v_f^in⟩(S)|`
- Plot the three curves.
- For the layer near `S = 2`, plot `J_in`, `⟨ρ_f^in⟩`, and `⟨v_f^in⟩` as functions of `N`.

### Implementation Implication
- The simulator must preserve radial-profile samples at snapshot times.
- The analysis layer must separate:
  - density averaging over time samples
  - normal-velocity averaging over valid inward particles only
- The first physically accessible shell is near `S = 2` because particle centers cannot enter the obstacle. This repository fixes the near-shell convention as `[2.0, 2.2)`.

## Direct Implications for the Repository
- `tp3 system1 run --config ...` remains the single-realization simulator.
- `tp3 system1 study --config ...` is responsible for generating the datasets and figures needed to answer `1.1–1.4`.
- `tp3 system1 package-delivery --output ...` exists because the statement imposes a compact final zip containing only the motor.
- The current repository treats plotting and post-processing as local study tools, but excludes them from the delivery package.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Observable: System 1 Measurements](system_1_observables.md)
- [Analysis: Animation Output Contract](animation_output_contract.md)
- [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md)
- [Analysis: Deliverable Formatting Requirements](deliverables_format_requirements.md)
