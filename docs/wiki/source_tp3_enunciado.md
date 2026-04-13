---
type: "source"
title: "Source: TP3 Enunciado"
summary: "Official assignment statement defining deliverables, event-driven scope, geometries, and observables."
tags: ["source", "tp3", "requirements"]
source_path: "docs/raw/TP3_Enunciado.pdf"
last_updated: "2026-04-13"
---
# Source: TP3 Enunciado

**File**: [TP3_Enunciado.pdf](../raw/TP3_Enunciado.pdf)  
**Date Ingested**: 2026-04-13  
**Subject**: Simulación Dirigida por Eventos (SDS - TP3)

## Summary
This document is the primary source of truth for the assignment. It defines the two candidate systems, fixes the required observables, and constrains deliverables and file naming. For this repository, it anchors the implementation of [System 1: Scanning Rate](system_1_scanning_rate.md) and the deliverable guidance summarized in [Analysis: Deliverable Formatting Requirements](deliverables_format_requirements.md).

## Key Requirements Extracted
- The simulation engine must be event-driven.
- The engine must write text output that an external animation module can replay independently.
- For `Sistema 1`, the domain is a circular enclosure of diameter `80 m` with a fixed central obstacle of radius `1 m`.
- For `Sistema 1`, particles start fresh, become used on center contact, and become fresh again on outer-boundary contact.
- The final code delivery must contain only the simulation motor and remain under `100 KB` zipped.

## Deliverables and Constraints
- Oral presentation of `13` minutes.
- PDF version of the presentation with representative still frames plus explicit links for animations.
- Zip file with source code only, excluding outputs, figures, post-processing, and documentation extras.
- Delivery deadline stated as `2026-04-24 10:00`.

## Related Pages
- [System 1: Scanning Rate](system_1_scanning_rate.md)
- [System 2: Smart Queues](system_2_smart_queues.md)
- [Observable: System 1 Measurements](system_1_observables.md)
- [Analysis: Animation Output Contract](animation_output_contract.md)
