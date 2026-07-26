# PAIOS

Personal AI Operating System

---

## Vision

Provider-independent AI platform.

---

## Repository

- docs
- core
- sdk
- plugins

---

## Source Tree Layout (Phase 1)

Per `docs/920_Phase1_Work_Breakdown.md` (WP-01), Phase 1 source code lives
under `src/paios/`, with one top-level package per Phase 1 component area:

- `src/paios/kernel` — Core Kernel
- `src/paios/registry` — Service Registry
- `src/paios/events` — Event Bus
- `src/paios/context` — Context Manager
- `src/paios/memory` — Memory Manager
- `src/paios/storage` — Storage Interface
- `src/paios/providers` — Provider Interface
- `src/paios/config` — Configuration Manager
- `src/paios/logging` — Logging Interface

Each package's public interface, implementation(s), and error types are
colocated within that package, per
`docs/930_Phase1_Development_Workflow.md`. Tests live under `tests/`. No
new top-level package is added outside this set without first amending
this convention in its own reviewed pull request.

---

## Development Flow

main

↓

dev

↓

feature/*

---

## Status

Architecture Phase

