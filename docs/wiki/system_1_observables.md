---
type: "observable"
title: "Observable: System 1 Measurements"
summary: "Detailed measurement contract for TP3 points 1.1-1.4, including runtime, scanning rate, stationary used fraction, and radial profiles."
tags: ["observable", "system1", "statistics"]
sources: ["source_tp3_enunciado.md", "source_teorica_0.md", "source_guia_presentaciones.md"]
last_updated: "2026-04-17"
---
# Observable: System 1 Measurements

The repository now supports the full measurement surface required by the statement, not just the raw motor state.

## 1.1 Runtime vs N
- Absolute simulation horizon fixed at `tf = 500 s` (see [errata](source_tp3_enunciado.md#errata-cátedra)).
- Runtime is measured as wall-clock time of the full motor execution, including snapshot writing.
- Default study policy:
  - `5` repetitions per `N`
  - mean and standard deviation reported
  - if `counts_mode = auto`, stop exploring larger `N` after the median runtime exceeds `20 s`

## 1.2 Scanning Rate
- Preserve the full `C_fc(t)` series of `fresh -> used` center contacts.
- Always include the initial point `(0, 0)`.
- Compute `J` per realization using OLS slope over the full `C_fc(t)` series in physical time.
- Aggregate `⟨J⟩(N)` and standard deviation across realizations.

## 1.3 Used Fraction
- Preserve snapshot history of `F_u(t) = N_u(t)/N`.
- Resample with zero-order hold on a uniform grid with `Δt = 0.5 s`.
- Detect stationarity using the protocol defined in [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md).
- Report:
  - `t_stationary(N)`
  - `F_est(N)`
  - number of realizations that did or did not reach stationarity before the safety cutoff

## 1.4 Radial Profiles
- Shell width fixed at `dS = 0.2 m`.
- Restrict the sample to fresh particles with `R · v < 0`.
- Density averaging:
  - compute shell density at each sampled time
  - average over post-stationary time samples
  - then average across realizations
- Normal velocity averaging:
  - average only across valid inward particles
  - do not inject artificial zeros when a shell is empty
- Derived flux:
  - `J_in(S) = <ρ_f^in>(S) |<v_f^in>(S)|`

## Output Products from `tp3 system1 study`
- Raw realization files under `raw/`
- Snapshot outputs under `runs/`
- Aggregate CSVs under `aggregates/`
- PNG figures under `figures/`
- Markdown summary under `summary.md`

## Related Pages
- [Source: TP3 Enunciado](source_tp3_enunciado.md)
- [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md)
- [Analysis: Animation Output Contract](animation_output_contract.md)
