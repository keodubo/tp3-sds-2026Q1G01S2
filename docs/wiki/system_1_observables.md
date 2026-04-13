---
type: "observable"
title: "Observable: System 1 Measurements"
summary: "Required TP3 observables for System 1, including scanning rate, used fraction, radial profiles, and execution-time scaling."
tags: ["observable", "system1", "statistics"]
sources: ["source_tp3_enunciado.md", "source_teorica_0.md", "source_guia_presentaciones.md"]
last_updated: "2026-04-13"
---
# Observable: System 1 Measurements

The current engine foundation already accumulates the raw ingredients for the main `Sistema 1` observables, even though plotting and sweep orchestration are intentionally left outside v1.

## Required Measurements
1. Execution time versus `N` for fixed absolute simulation time `tf = 5 s`.
2. `C_fc(t)`: cumulative number of fresh particles that contacted the center and changed state.
3. `J`: slope of a linear interpolation of `C_fc(t)`.
4. `F_u(t) = N_u(t)/N`: used-particle fraction versus time.
5. `F_est`: stationary used fraction.
6. Radial profiles of inward fresh particles:
   - `⟨ρ_f^in⟩(S)`
   - `⟨v_f^in⟩(S)`
   - `J_in(S) = ⟨ρ_f^in⟩(S) |⟨v_f^in⟩(S)|`

## Averaging Rules to Preserve
- Run multiple realizations with different random seeds for stochastic summaries.
- Report mean values with standard deviations or error bars where applicable.
- Do not print more significant digits than the uncertainty justifies, as stressed in [Source: Teorica 0](source_teorica_0.md).

## Radial-Profile Selection
- Use concentric shells around the central obstacle.
- Restrict the sample to fresh particles whose radial velocity points inward.
- Average density and normal velocity across sampled times and realizations.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Source: TP3 Enunciado](source_tp3_enunciado.md)
- [Source: Teorica 0](source_teorica_0.md)
- [Source: Guia Presentaciones](source_guia_presentaciones.md)
