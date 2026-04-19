---
type: "administration"
title: "Wiki Log"
summary: "Chronological record of wiki operations."
tags: ["administration", "log"]
last_updated: "2026-04-19"
---
# Wiki Log

Chronological record of knowledge ingestion and synthesis operations.

## [2026-04-13] setup | Persistent Wiki Initialized
- Created the `docs/raw/` and `docs/wiki/` layer separation.
- Added the schema in `CLAUDE.md`.
- Seeded the initial TP3 pages.

## [2026-04-13] ingest | TP3 Enunciado
- Consolidated the assignment requirements into [Source: TP3 Enunciado](source_tp3_enunciado.md).
- Anchored the two system pages and the event-driven framing.

## [2026-04-13] ingest | Molecular Dynamics Simulation of Hard Spheres
- Ingested the hard-sphere reference in [Source: Molecular Dynamics Simulation of Hard Spheres](source_molecular_dynamics_simulation_of_hard_spheres.md).
- Used it to strengthen [Concept: Hard-Sphere Collision Model](collision_model.md) and [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md).

## [2026-04-13] ingest | Teoricas 0-3
- Ingested [Source: Teorica 0](source_teorica_0.md), [Source: Teorica 1](source_teorica_1.md), [Source: Teorica 2](source_teorica_2.md), and [Source: Teorica 3](source_teorica_3.md).
- Updated system, concept, and observable pages with statistical, event-driven, and modeling context.

## [2026-04-13] ingest | Guias de Formato
- Ingested [Source: Guia Informes](source_guia_informes.md) and [Source: Guia Presentaciones](source_guia_presentaciones.md).
- Consolidated submission expectations into [Analysis: Deliverable Formatting Requirements](deliverables_format_requirements.md).

## [2026-04-13] refactor | Python Foundation and Wiki Tooling
- Added the `tp3` Python package with CLI support for wiki maintenance and System 1 execution.
- Added the initial event-driven hard-sphere engine foundation and its tests.
- Standardized the wiki on frontmatter plus generated index sections.

## [2026-04-13] refactor | TP3 Detailed System 1 Study Pipeline
- Re-ingested [Source: TP3 Enunciado](source_tp3_enunciado.md) with detailed sections for deliverables, output contract, and points 1.1-1.4.
- Added [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md) to lock the study methodology used by the repository.
- Extended the System 1 wiki pages so they match the implemented `run`, `study`, and `package-delivery` workflows.

## [2026-04-13] run | System 1 simulation
- Executed `tp3 system1 run --config /Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/configs/system1.example.toml`.
- Generated output: `/Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/artifacts/system1/example_run.txt`.
- Processed events: 2.

## [2026-04-13] run | System 1 study
- Executed `tp3 system1 study --config /Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/configs/system1.study.example.toml`.
- Study root: `/Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/artifacts/system1/studies/example-study`.
- Particle counts: [8, 12].

## [2026-04-19] run | System 1 simulation
- Executed `tp3 system1 run --config /Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/configs/system1.example.toml`.
- Generated output: `/Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/artifacts/system1/example_run.txt`.
- Processed events: 140.
