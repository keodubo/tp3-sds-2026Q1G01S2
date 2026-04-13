---
type: "administration"
title: "Wiki Index"
summary: "Catalog of wiki pages grouped by type."
tags: ["administration", "index"]
last_updated: "2026-04-13"
---
# Wiki Index

This index is a catalog of all knowledge synthesized from source documents.

## Systems
- [System 1: Scanning Rate](system_1_scanning_rate.md) - Hard-sphere event-driven dynamics in a circular enclosure, with stateful particles, explicit color output, and a study pipeline for TP3 points 1.1-1.4.
- [System 2: Smart Queues](system_2_smart_queues.md) - Alternative TP3 system based on event-driven queueing, server assignment, and spatial queue organization.

## Concepts
- [Concept: Event Queue and Lazy Invalidation](event_queue_lazy_invalidation.md) - Priority-queue scheduling strategy where stale events remain queued and are discarded when popped.
- [Concept: Event-Driven Simulation](event_driven_simulation.md) - Simulation scheme where state updates occur only when a discrete event happens.
- [Concept: Hard-Sphere Collision Model](collision_model.md) - Collision-time prediction and elastic collision rules for particles, the outer enclosure, and the central obstacle.

## Observables
- [Observable: System 1 Measurements](system_1_observables.md) - Detailed measurement contract for TP3 points 1.1-1.4, including runtime, scanning rate, stationary used fraction, and radial profiles.

## Sources
- [Source: Guia Informes](source_guia_informes.md) - Formatting guide for the written report, with rules on structure, technical language, figures, equations, and references.
- [Source: Guia Presentaciones](source_guia_presentaciones.md) - Formatting guide for oral presentations and slide decks, including section order, animation handling, and evidence requirements.
- [Source: Molecular Dynamics Simulation of Hard Spheres](source_molecular_dynamics_simulation_of_hard_spheres.md) - Reference note on event-driven hard-disc simulation, collision prediction, collision resolution, and lazy invalidation.
- [Source: Teorica 0](source_teorica_0.md) - Lecture notes on stochastic simulation reporting, repeated realizations, sample error, histograms, and regression framing.
- [Source: Teorica 1](source_teorica_1.md) - Lecture notes positioning molecular dynamics within many-particle systems and numerical simulation.
- [Source: Teorica 2](source_teorica_2.md) - Lecture notes on cellular automata, lattice gas models, and off-lattice agent systems; useful mainly as a modeling contrast.
- [Source: Teorica 3](source_teorica_3.md) - Lecture notes on event-driven molecular dynamics of rigid spheres, including initialization, collision-time prediction, and collision operators.
- [Source: TP3 Enunciado](source_tp3_enunciado.md) - Detailed assignment source covering deliverables, System 1 physics, required studies 1.1-1.4, and constraints on the final code package.

## Analyses
- [Analysis: Animation Output Contract](animation_output_contract.md) - Plain-text output contract for System 1, now including explicit RGB color per particle to satisfy the TP statement.
- [Analysis: Deliverable Formatting Requirements](deliverables_format_requirements.md) - Operational checklist distilled from the report and presentation format guides.
- [Analysis: System 1 Experimental Protocol](system_1_experimental_protocol.md) - Repository protocol for selecting N, detecting stationarity, defining averages, and handling the near-shell S≈2 analysis.

## Decisions
- [Decision: V1 Foundation Scope](decision_v1_foundation_scope.md) - The repository targets Python, manual assisted wiki ingest, and System 1 as the code implementation priority.

## Administration
- [Wiki Log](log.md) - Chronological record of wiki operations.
