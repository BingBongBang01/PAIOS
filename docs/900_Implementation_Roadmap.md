# 900_Implementation_Roadmap

Status: Draft

Version: 0.1

Owner: PAIOS

---

## Purpose

This document defines the **build order** for PAIOS. It does not describe architecture, interfaces, or design decisions — those are owned by `docs/000_Project_Constitution.md` and the architecture documents `010`–`110`. This roadmap answers one question only: *in what sequence should each component be implemented so that every dependency exists before the component that needs it?*

All architectural authority remains with the referenced documents. Where this roadmap and an architecture document appear to disagree, the architecture document wins, and this roadmap should be corrected.

---

## Scope

In scope:
- Ordering of implementation work across the full system, grouped into phases.
- Definition-of-Done criteria per phase, used as phase-exit gates.
- Mapping of roadmap phases to GitHub milestones and issues.
- Known risks to the sequencing itself.

Out of scope (see referenced docs instead):
- Component design, interfaces, or data models (`010`–`110`).
- Governing principles and non-negotiables (`000_Project_Constitution.md`).
- Product philosophy and rationale (`001_Project_Philosophy.md`).

---

## Development Strategy

PAIOS is built bottom-up, honoring the constitution's Interface-First and Plugin-First principles: every layer is built against the interfaces defined by the layer below it, never against a concrete implementation. This allows later phases (AI Layer, Plugin Platform, User Layer) to proceed against stable contracts while lower layers are still hardened.

Each phase must produce working, tested software before the next phase starts substantive integration work — but phases may overlap at the edges (e.g., Plugin SDK scaffolding may begin once the Capability Model interfaces are frozen, without waiting for full AI Layer completion). Strict sequencing applies to *dependencies*, not to *calendar time*.

---

## Dependency Graph

Derived from the interfaces and dependencies described in `010`–`110`:

```
Repository
  └─ Core Kernel (010)
       ├─ Event Model (040)
       ├─ Capability Registry (030)
       └─ Storage Architecture (070)
              └─ Memory Model (050)
                     └─ Knowledge Graph (060)
                            └─ Context Pipeline (020)
                                   └─ Prompt Builder (090)
                                          └─ AI Router (080)
                                                 └─ Plugin SDK (100)
                                                        └─ Workflow Engine (110)
                                                               └─ User Layer (CLI / Desktop UI / Settings)
                                                                      └─ Integration Layer (Local Models / Cloud Providers / Connectors)
                                                                             └─ Quality Layer (Tests / Benchmarks / Doc Review)
```

No component may be implemented ahead of the components it depends on in this graph, per the Interface-First principle in `000_Project_Constitution.md`.

---

## Phase 1 - Foundation

- **Repository** — project scaffolding, license, contribution guidelines, CI skeleton.
- **Core Kernel** — Configuration Service, DI Container, Event Bus, Module Lifecycle Manager, Error Boundary. See `010_Core_Kernel.md`.
- **Event Model** — event vocabulary, schema, versioning, retry/dead-letter policy riding on the Kernel's Event Bus. See `040_Event_Model.md`.
- **Context Pipeline** — request/response flow scaffolding (interfaces only at this phase). See `020_Context_Pipeline.md`.
- **Memory Model** — Working/Long-Term/Semantic/Episodic memory interfaces and Retrieval API. See `050_Memory_Model.md`, backed by `070_Storage_Architecture.md`.

**Definition of Done**
- Kernel boots with DI Container, Event Bus, and Configuration Service operational.
- Event schema is versioned and documented; a sample event round-trips through the bus.
- Storage Architecture's `StorageProvider` interface has at least one working implementation.
- Memory Model's Retrieval API returns results against the storage-backed implementation.
- Context Pipeline stages exist as interfaces with stub implementations, wired to the Event Bus.
- All Phase 1 components pass unit tests; no component in this phase depends on anything outside it.

---

## Phase 2 - AI Layer

- **AI Router** — provider dispatch, model selection, failover, streaming. See `080_AI_Router.md`.
- **Prompt Builder** — template resolution, variable injection, context merge, safety filtering. See `090_Prompt_Builder.md`.
- **Provider Adapter** — first concrete `AIProvider` implementation(s), registered via the Kernel's DI Container.
- **Embedding** — embedding generation path feeding Knowledge Graph and semantic memory (`060_Knowledge_Graph.md`, `050_Memory_Model.md`).
- **Memory Integration** — Context Pipeline wired to live Memory Model and Knowledge Graph retrieval, replacing Phase 1 stubs.

**Definition of Done**
- Context Pipeline produces a real prompt via Prompt Builder using live memory retrieval.
- AI Router dispatches to at least one Provider Adapter and returns a streamed response end-to-end.
- Embedding generation populates Knowledge Graph entities/relationships from semantic memory writes.
- Failover and retry policy in AI Router are exercised by an integration test.

---

## Phase 3 - Plugin Platform

- **Plugin SDK** — SDK API surface (events, memory, graph, prompt, storage, UI), manifest format. See `100_Plugin_SDK.md`.
- **Plugin Loader** — plugin lifecycle manager, sandboxing, permission gate.
- **Capability Registry** — capability registration/discovery, versioning, permission model. See `030_Capability_Model.md`.
- **Workflow Engine** — step execution graph, scheduler, triggers, conditions, recovery. See `110_Workflow_Engine.md`.

**Definition of Done**
- A sample plugin registers a capability through the Capability Registry and is discoverable at runtime.
- Plugin Loader enforces the permission gate and sandbox boundary against a plugin that attempts an unauthorized action.
- Workflow Engine executes a multi-step workflow that invokes at least one plugin-provided capability, including a failure/recovery path.

---

## Phase 4 - User Layer

- **CLI** — command-line entry point exercising Kernel, Context Pipeline, and AI Router.
- **Desktop UI** — first user-facing surface, consuming the same interfaces as the CLI.
- **Settings** — user-facing configuration surface backed by the Kernel's Configuration Service.
- **Configuration** — configuration schema, validation, and persistence, extending `010_Core_Kernel.md`.
- **Logging** — structured logging across Kernel, Event Model, and AI Router, for both CLI and Desktop UI consumption.

**Definition of Done**
- CLI and Desktop UI both complete a full request → context assembly → AI response round trip using only public interfaces.
- Settings changes persist through Configuration and are observable by both surfaces without restart, where the Kernel's lifecycle model allows it.
- Logs from a single request are traceable end-to-end across Kernel, Event Model, and AI Router.

---

## Phase 5 - Integration

- **Local Models** — on-device provider adapter(s) added to the AI Router, per Provider Independence in `000_Project_Constitution.md`.
- **Cloud Providers** — additional cloud-based provider adapter(s).
- **Connectors** — external data source integrations exposed through the Plugin SDK / Capability Registry.
- **External APIs** — outbound integrations consumed by Workflow Engine triggers or plugin capabilities.

**Definition of Done**
- At least one local and one cloud provider are both selectable through the AI Router's Model Selector without code changes to calling layers.
- At least one Connector round-trips data into Memory Model / Knowledge Graph through the Plugin SDK.
- An External API integration is triggered by a Workflow Engine trigger and completes successfully, including its failure path.

---

## Phase 6 - Quality

- **Unit Tests** — coverage across all components introduced in Phases 1-5.
- **Integration Tests** — cross-component flows: Kernel → Context Pipeline → AI Router, and Plugin SDK → Workflow Engine.
- **Benchmark** — performance baselines for context assembly latency, AI Router dispatch latency, and Memory retrieval latency.
- **Documentation Review** — verification that `000`-`110` and this roadmap remain accurate against the shipped implementation.

**Definition of Done**
- Unit and integration test suites pass in CI for every component across Phases 1-5.
- Benchmark results are recorded and compared against the previous milestone.
- Documentation Review confirms no drift between architecture documents and implemented behavior; discrepancies are filed as issues, not silently fixed in docs.

---

## Milestones

| Milestone | Phase(s) | Exit Criteria |
|---|---|---|
| M1 - Bootable Kernel | Phase 1 | Definition of Done for Phase 1 met |
| M2 - First AI Response | Phase 2 | Definition of Done for Phase 2 met |
| M3 - Extensible Platform | Phase 3 | Definition of Done for Phase 3 met |
| M4 - Usable Product | Phase 4 | Definition of Done for Phase 4 met |
| M5 - Multi-Provider System | Phase 5 | Definition of Done for Phase 5 met |
| M6 - Release Candidate | Phase 6 | Definition of Done for Phase 6 met |

---

## GitHub Issues Mapping

- One GitHub Milestone per roadmap Milestone (M1-M6).
- One GitHub Issue per bullet item within a phase (e.g., "Phase 1: Core Kernel", "Phase 2: Provider Adapter").
- Each issue references the corresponding architecture document section instead of restating it, e.g. "Implements interfaces defined in `docs/010_Core_Kernel.md`".
- Cross-phase dependencies are recorded as GitHub Issue "blocked by" links matching the Dependency Graph above, so Claude Code and human contributors can query blocking status directly from GitHub rather than from this document.

---

## Risks

- **Architecture documents are still drafts (`Status: Draft`, many sections `TBD`).** Implementation started against an interface may need rework once a `TBD` section is finalized. Mitigate by freezing interfaces per component before starting its phase, and treating interface changes mid-phase as a roadmap update, not silent scope creep.
- **Phase overlap ambiguity.** Allowing phases to overlap at the edges (see Development Strategy) risks components being built against unstable upstream interfaces. Mitigate by requiring the upstream component's Definition of Done to be met before overlap work merges to the main branch.
- **Undocumented User Layer and Integration Layer architecture.** No `0XX` document currently exists for CLI, Desktop UI, Settings, Logging, Connectors, or External APIs. Mitigate by authoring the missing architecture documents before or during Phase 4/5, not after.
- **Provider Independence drift.** Phase 2 introduces the first Provider Adapter; if implementation couples the AI Router to that provider's specifics, Phase 5's multi-provider goal becomes a rewrite rather than an extension. Mitigate by requiring a second, even minimal, provider adapter before Phase 2 is marked done.

---

## Future Work

- Author missing architecture documents for User Layer (CLI, Desktop UI, Settings, Logging) and Integration Layer (Connectors, External APIs) referenced in Phases 4-5, following the numbering convention (`120_...`, `130_...`, etc.).
- Revisit this roadmap once `000`-`110` move from `Status: Draft` to a finalized status, to confirm phase ordering still holds.
- Define a deprecation/versioning roadmap for Plugin SDK and Capability Model once the Plugin Platform (Phase 3) ships its first stable version.
