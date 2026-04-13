# Persistent Wiki and System 1 Schema

This repository is organized as a persistent wiki plus a Python implementation foundation for `Sistema 1) Scanning rate en recinto cerrado con obstáculo fijo`.

## Core Layers
1. `docs/raw/`: immutable source material. Never rewrite or move files from tooling.
2. `docs/wiki/`: LLM-maintained synthesis layer in markdown.
3. `src/tp3_sds/`: deterministic helper code for wiki maintenance and the System 1 simulation engine.

## Wiki Contract
Every wiki page must have YAML frontmatter with this minimum shape:

```yaml
---
type: "concept"
title: "Concept: Event-Driven Simulation"
summary: "One-line summary used by docs/wiki/index.md."
tags: ["concept", "system1"]
sources: ["source_tp3_enunciado.md", "source_teorica_3.md"]
last_updated: "2026-04-13"
---
```

Supported `type` values:
- `source`
- `system`
- `concept`
- `observable`
- `analysis`
- `decision`
- `administration`

## Agent Workflows

### Ingest
1. Read one source from `docs/raw/`.
2. If useful, run `PYTHONPATH=src python3 -m tp3_sds wiki scaffold-source <raw-path>`.
3. Replace the scaffold with a real synthesized summary page.
4. Update the affected system, concept, observable, analysis, or decision pages.
5. Run `PYTHONPATH=src python3 -m tp3_sds wiki refresh-index`.
6. Run `PYTHONPATH=src python3 -m tp3_sds wiki lint`.
7. Append the final ingest result to `docs/wiki/log.md`.

### Query
1. Search `docs/wiki/index.md` first.
2. Use `PYTHONPATH=src python3 -m tp3_sds wiki search "<query>"` when the wiki grows.
3. Answer from wiki pages first, then drill down into raw sources only if needed.
4. If the answer is reusable, file it back into `docs/wiki/` as `analysis` or `decision`.

### Lint
Run `PYTHONPATH=src python3 -m tp3_sds wiki lint` to detect:
- broken wiki links
- orphan pages
- missing index entries
- stale raw-source references
- citation placeholders left in the wiki

## System 1 Code Contract
- Runtime stack: Python 3.11+.
- Config format: TOML.
- CLI entrypoint: `tp3`.
- Output contract: header with run metadata and geometry, then repeated steps of `{event_id, time, N_used}` followed by particle lines `id, x, y, vx, vy, state`.
- Output artifacts live outside `docs/raw/`, currently under `artifacts/`.

## System 1 Boundaries
The first implementation covers:
- event-driven hard-sphere motion in a circular enclosure with a fixed circular obstacle
- particle-particle collisions
- outer-boundary and inner-obstacle collisions
- fresh/used state transitions
- snapshot writing for the animator
- observable accumulation hooks for scanning rate, used fraction, and radial profiles

The first implementation does not cover:
- plotting
- batch experiment orchestration
- post-processing pipelines
- `Sistema 2` execution
