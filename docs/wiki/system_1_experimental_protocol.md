---
type: "analysis"
title: "Analysis: System 1 Experimental Protocol"
summary: "Repository protocol for selecting N, detecting stationarity, defining averages, and handling the near-shell S≈2 analysis."
tags: ["analysis", "system1", "protocol", "statistics"]
sources: ["source_tp3_enunciado.md", "source_teorica_0.md", "source_guia_presentaciones.md"]
last_updated: "2026-04-17"
---
# Analysis: System 1 Experimental Protocol

The statement requires stationary metrics and radial averages, but it does not specify the protocol to obtain them. This page fixes the repository-level study contract used by `tp3 system1 study`.

## Particle-Count Selection
- If a study config provides an explicit list of `N`, use it as-is.
- If `counts_mode = auto`, use the default staircase from the study config.
- Stop extending the staircase after the median runtime for the current `N` exceeds `20 s` per realization.
- The production `N` grid adopted by this repository is `[10, 50, 100, 200, 400, 800]`. The file `configs/system1.study.example.toml` ships with this grid and `generate_all.sh` consumes it by default.

## Runtime Study (1.1)
- Use fixed physical horizon `tf = 500 s` (see [errata](source_tp3_enunciado.md#errata-cátedra)).
- Repeat each `N` five times by default.
- Report mean and standard deviation of wall-clock runtime.

## Stationary Detection for 1.3 and 1.4
- Resample `F_u(t)` with zero-order hold on a uniform grid with `Δt = 0.5 s`.
- Define two consecutive windows of length `10 s`.
- Re-check every `5 s`.
- Declare stationarity when the absolute difference between the window means is at most `0.02` for `3` consecutive checks.
- After detecting stationarity, extend the run by `20 s` to measure stationary observables.
- Safety cutoff:
  - terminate a realization at `t_max = 2000 s`
  - if stationarity is not reached by then, mark the realization `no_stationary`

## Averaging Rules
- `J` is averaged across realizations at fixed `N`.
- `F_est` is averaged only across realizations that satisfy the stationary protocol.
- Shell density is averaged over all selected time samples, so empty shells contribute zero density at that time.
- Shell normal velocity is averaged only over valid inward particles, so empty shells do not inject artificial zeros into the velocity average.

## Near-Shell Convention
- The statement asks for the layer near `S = 2`.
- Since the obstacle radius is `1 m` and the particle radius is `1 m`, the first accessible shell starts at `S = 2`.
- This repository fixes the near-shell used in the `vs N` plots as `[2.0, 2.2)`.

## Related Pages
- [Source: TP3 Enunciado](source_tp3_enunciado.md)
- [Observable: System 1 Measurements](system_1_observables.md)
- [System 1: Scanning Rate](system_1_scanning_rate.md)
