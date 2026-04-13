---
type: "decision"
title: "Decision: V1 Foundation Scope"
summary: "The repository targets Python, manual assisted wiki ingest, and System 1 as the code implementation priority."
tags: ["decision", "scope", "system1", "python"]
sources: ["source_tp3_enunciado.md", "source_teorica_3.md", "source_guia_presentaciones.md"]
last_updated: "2026-04-13"
---
# Decision: V1 Foundation Scope

This repository intentionally optimizes for a safe first implementation rather than for full TP automation.

## Chosen Defaults
- Code target: [System 1: Scanning Rate](system_1_scanning_rate.md).
- Language: Python.
- Wiki workflow: manual ingest, but assisted by deterministic CLI helpers.
- Output: plain-text snapshots for an external animator.
- Out of scope for v1: batch experiment sweeps, plotting, post-processing pipelines, and `Sistema 2` execution.

## Why
- The event-driven hard-sphere engine is the riskiest technical part and benefits from early stabilization.
- A persistent wiki helps keep the theoretical and format constraints visible while implementation advances.
- Python keeps the simulation and the repo tooling in one place with low ceremony.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [Analysis: Animation Output Contract](animation_output_contract.md)
- [Analysis: Deliverable Formatting Requirements](deliverables_format_requirements.md)
