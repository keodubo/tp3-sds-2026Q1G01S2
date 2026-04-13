---
type: "system"
title: "System 2: Smart Queues"
summary: "Alternative TP3 system based on event-driven queueing, server assignment, and spatial queue organization."
tags: ["system", "system2", "queues", "event-driven"]
sources: ["source_tp3_enunciado.md", "source_teorica_0.md", "source_teorica_3.md"]
last_updated: "2026-04-13"
---
# System 2: Smart Queues

`Sistema 2` remains documented in the wiki but is out of scope for the current code implementation. It stays relevant because the wiki schema and the general event-driven concepts are shared with [Concept: Event-Driven Simulation](event_driven_simulation.md).

## Problem Shape
- Square domain `30 x 30 m^2`.
- Poisson arrivals with mean inter-arrival time `t1`.
- Between `1` and `k` servers placed on a border.
- Event-driven queue motion and service completion.

## Design Degrees of Freedom
- Assignment to servers depends probabilistically on distance and queue length.
- Queue layout can be guided or free-form.
- Two operating modes must be compared: one queue per server versus one shared queue.

## Required Outputs
- Average queue length or growth rate.
- Residence-time distributions.
- Comparative analysis between queue modalities.

## Relevance to This Repo
- It validates that the wiki tooling should remain system-agnostic.
- It shares statistical reporting needs with [Source: Teorica 0](source_teorica_0.md).
- It shares the event-driven framing with [Source: Teorica 3](source_teorica_3.md).
