# 920_Phase1_Work_Breakdown

Status: Draft

Version: 0.1

Owner: PAIOS

---

## Purpose

This document decomposes
[910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
into the smallest independently implementable work packages (WPs) for Phase
1, sized so that each is completable in one pull request. It does not
introduce new architecture or interfaces — every interface, event,
configuration key, and error type referenced below is defined in `910`, and
every work package cites the exact section of `910` (or of `000`/`900`) it
implements rather than restating it.

Work packages are ordered so that, applied in sequence, the repository
compiles and passes its existing tests after every single merge — no work
package leaves the tree in a broken or partially-typed state, and no work
package depends on a component scheduled for Phase 2 or later.

---

## Numbering and Conventions

- IDs are `WP-01` through `WP-20`, in merge order.
- "Files Expected" gives the expected file/module grouping, not exact
  paths — Phase 1 has not yet fixed a source-tree layout (a gap noted in
  [901_Architecture_Audit_Report](901_Architecture_Audit_Report.md#suggested-repository-changes)),
  so paths are described by responsibility (e.g. `kernel/`, `storage/`,
  `memory/`) for the implementer to place consistently with whatever
  layout WP-01 establishes.
- "Public Interfaces" lists only the interface/type names each WP
  introduces or extends, per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md);
  it does not repeat full signatures already given there.
- Every WP that adds a module participating in the `Module` lifecycle
  (per [010_Core_Kernel](010_Core_Kernel.md#module-lifecycle)) is
  responsible for its own unit tests; cross-module integration tests are
  concentrated in WP-19 and WP-20 to keep earlier PRs small.

---

## Work Packages

### WP-01 — Repository Scaffolding

**Objective:** Establish the buildable, lintable, CI-checked empty
repository skeleton that every subsequent work package builds on.

**Scope:** Project scaffolding, license, contribution guidelines, CI
skeleton (build + lint + test job, no components yet), source-tree layout
convention (one top-level module/package per Phase 1 component area:
kernel, events, memory, storage, providers, config, logging, context), and
an empty entry point that compiles/builds successfully with zero
components wired in. Matches the Roadmap's Phase 1 "Repository" bullet,
per [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation).

**Files Expected:** repository root config (build/lint/test tooling
config), `LICENSE`, `CONTRIBUTING.md` (already exists — verify, do not
duplicate), CI workflow definition, an empty top-level entry-point module,
one empty placeholder directory per component area listed above.

**Dependencies:** None.

**Public Interfaces:** None — no component interfaces are introduced in
this WP.

**Acceptance Criteria:**
- CI runs on every PR and passes on an empty/no-op change.
- The repository builds and its (currently empty) test suite runs
  successfully in CI.
- Source-tree layout convention is documented in a short root-level note
  (e.g. a section in `README.md`) so every later WP places files
  consistently.

**Tests Required:** A trivial "CI smoke test" (e.g. one placeholder test
that always passes) to prove the test runner itself is wired into CI.

**Estimated Complexity:** S

**Blocking Issues:** None.

**Follow-up Tasks:** WP-02 through WP-20 all depend on this WP's layout
convention and CI wiring.

---

### WP-02 — Configuration Manager

**Objective:** Implement the `ConfigurationManager` interface and its
load/validate/merge behavior, per
[910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#configuration-manager).

**Scope:** `ConfigurationManager` interface (`get`, `getRequired`,
`isLoaded`); configuration source merge in the fixed precedence order
`defaults < file < environment`; schema validation that halts with
`ConfigurationError(key, reason)` on failure; fixed load conventions
(`paios.config.json` file path, `PAIOS_` environment variable prefix). Does
not include wiring into Kernel boot (that is WP-05); this WP delivers the
Configuration Manager as a standalone, fully unit-testable module.

**Files Expected:** `config/` module: interface, implementation, schema
definitions, error types.

**Dependencies:** WP-01.

**Public Interfaces:** `ConfigurationManager`, `ConfigurationError`.

**Acceptance Criteria:**
- Loading valid configuration from all three sources merges with the
  documented precedence.
- Missing a required schema key halts with `ConfigurationError` rather
  than returning a partially-loaded object.
- `get()` returns a provided default when a key is absent and not
  required; `getRequired()` throws `UnknownConfigKeyError` for a key not
  covered by the schema, per
  [910](910_Phase1_Core_Foundation_Specification.md#error-handling-6).

**Tests Required:** Unit tests for merge precedence, schema validation
success/failure, `get`/`getRequired`/`isLoaded` behavior, per
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy).

**Estimated Complexity:** S

**Blocking Issues:** None.

**Follow-up Tasks:** WP-05 (Kernel boot) wires this in as the first boot
phase.

---

### WP-03 — Service Registry

**Objective:** Implement the `ServiceRegistry` (DI Container) interface,
per
[910](910_Phase1_Core_Foundation_Specification.md#service-registry).

**Scope:** `ServiceRegistry` interface (`register`, `resolve`,
`isRegistered`); nominal `ServiceToken` type; singleton-lifetime,
single-binding-per-token semantics; `UnregisteredServiceError` and
`DuplicateRegistrationError`. No concrete Phase 1 component tokens are
registered in this WP — this WP delivers the registry mechanism itself,
standalone and testable with synthetic tokens.

**Files Expected:** `registry/` module: interface, implementation, token
type, error types.

**Dependencies:** WP-01.

**Public Interfaces:** `ServiceRegistry`, `ServiceToken`,
`UnregisteredServiceError`, `DuplicateRegistrationError`.

**Acceptance Criteria:**
- `register()` followed by `resolve()` for the same token returns the
  registered factory's instance.
- `resolve()` on an unregistered token throws `UnregisteredServiceError`.
- `register()` called twice for the same token throws
  `DuplicateRegistrationError`.
- `isRegistered()` correctly reports registration state.

**Tests Required:** Unit tests for the four acceptance criteria above
using synthetic test tokens, per
[910](910_Phase1_Core_Foundation_Specification.md#service-registry).

**Estimated Complexity:** XS

**Blocking Issues:** None.

**Follow-up Tasks:** WP-05 onward register every Phase 1 interface's token
here.

---

### WP-04 — Event Schema and Types

**Objective:** Define the `Event` type, schema registration mechanism, and
version-compatibility rules, per
[040_Event_Model](040_Event_Model.md#event-schema) and
[910](910_Phase1_Core_Foundation_Specification.md#event-bus).

**Scope:** `Event<P>` type (`id`, `type`, `version`, `timestamp`, `source`,
`correlationId`, `payload`); a schema registry keyed by `type` + `version`
(separate from the Service Registry — this is event-schema registration,
not dependency injection); payload validation function; `InvalidEventError`.
Does not include the bus transport itself (routing, delivery, retry) — that
is WP-05. This WP is pure data/schema and is independently testable without
any transport.

**Files Expected:** `events/` module: `Event` type, schema registry,
validation, error types.

**Dependencies:** WP-01.

**Public Interfaces:** `Event`, `EventSchemaRegistry` (internal to the
events module; not resolved via the Service Registry), `InvalidEventError`.

**Acceptance Criteria:**
- Registering a schema for a `type`/`version` pair and validating a
  matching payload succeeds.
- Validating a payload against an unregistered `type`/`version` or a
  schema-invalid payload raises `InvalidEventError`.
- Two different modules registering event types with different names
  cannot collide (schema registry is keyed by full `type` string,
  namespaced by owning module per
  [040_Event_Model](040_Event_Model.md#event-schema)).

**Tests Required:** Unit tests for schema registration, valid/invalid
payload validation, and namespacing collision avoidance.

**Estimated Complexity:** S

**Blocking Issues:** None.

**Follow-up Tasks:** WP-05 (Event Bus transport) depends on this WP's
types and validation function.

---

### WP-05 — Event Bus Transport

**Objective:** Implement the `EventBus` interface's routing, async
delivery, retry, and in-memory dead-letter handling (without persistence),
per
[910](910_Phase1_Core_Foundation_Specification.md#event-bus).

**Scope:** `EventBus` interface (`emit`, `subscribe`, `unsubscribe`);
routing by `type` and declared subscriber `versions`; asynchronous,
non-blocking delivery; exponential-backoff retry per
`eventBus.defaultRetryPolicy` or a type-specific policy; dead-letter
transition after retries exhausted, held in memory and emitted as
`EventDeadLettered`. Persisting dead-lettered events to the Storage
Interface is explicitly deferred to WP-10 (this WP's dead-letter path
holds state in memory only, which is sufficient for this WP's own unit
tests and does not block WP-06 through WP-09 from using the bus).

**Files Expected:** `events/bus/` module: `EventBus` implementation,
retry/backoff logic, in-memory dead-letter store.

**Dependencies:** WP-04.

**Public Interfaces:** `EventBus`, `EventHandler`, `EmitResult`,
`Subscription`, `EventDeadLettered` (event type).

**Acceptance Criteria:**
- `emit()` returns `"Routed"` when at least one version-compatible
  subscriber exists, `"Unrouted"` otherwise, without waiting for handler
  completion, per
  [040_Event_Model](040_Event_Model.md#async-execution).
- A failing handler is retried per its type's policy with exponential
  backoff and reaches `EventDeadLettered` once attempts are exhausted.
- A slow or failing subscriber does not block delivery to other
  subscribers of the same event.
- Two concurrent invocations of the same handler for a burst of same-type
  events are both accepted (handlers are assumed idempotent/concurrency-safe
  per [040_Event_Model](040_Event_Model.md#async-execution); this WP does
  not add locking around handler invocation).

**Tests Required:** Unit tests for routing, async non-blocking emit,
retry/backoff timing, dead-letter transition and event emission, per
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy).

**Estimated Complexity:** M

**Blocking Issues:** None.

**Follow-up Tasks:** WP-10 adds Storage-Interface-backed dead-letter
persistence. WP-06 (Kernel boot) wires this into Core Service Init.

---

### WP-06 — Module Lifecycle Manager and Error Boundary

**Objective:** Implement the `Module` lifecycle state machine and the
per-module Error Boundary, per
[010_Core_Kernel](010_Core_Kernel.md#module-lifecycle) and
[010_Core_Kernel](010_Core_Kernel.md#error-boundaries).

**Scope:** Internal `Module` interface (`init(context)`, `start()`,
`stop()`, `unload()`); the state machine
`Discovered → Initialized → Started → Stopped → Unloaded`, with `Failed`
reachable from `Initialized`/`Started`; Error Boundary wrapping each
module's init/start/stop/handler execution, containing faults and
emitting `ModuleFailed`. This WP delivers the lifecycle/error-boundary
mechanism against synthetic test modules — it does not yet drive any real
Phase 1 component (that begins in WP-07).

**Files Expected:** `kernel/lifecycle/` module: `Module` interface, state
machine, Error Boundary implementation.

**Dependencies:** WP-04 (for the `ModuleFailed` event type; the Module
Lifecycle Manager does not require the full bus transport to unit-test its
state machine, but does require an `EventBus` to emit `ModuleFailed` in its
integration path, so it also depends on WP-05).

**Public Interfaces:** `Module`, `ModuleFailed` (event type),
`ModuleState` enum.

**Acceptance Criteria:**
- A synthetic test module transitions through
  `Discovered → Initialized → Started → Stopped → Unloaded` correctly on
  successive lifecycle calls.
- A synthetic module whose `init()` throws transitions to `Failed` and
  emits `ModuleFailed` with `phase: "Initialized"`.
- A synthetic module whose running handler throws an unrecoverable error
  transitions to `Failed` from `Started` without affecting a second,
  independent synthetic module.
- Dependency order is respected on start (dependencies first) and stop
  (dependents first) for a small synthetic dependency graph.

**Tests Required:** Unit tests covering every transition in the state
diagram in
[010_Core_Kernel](010_Core_Kernel.md#module-lifecycle), and a fault
isolation test per
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy)
("Isolation test").

**Estimated Complexity:** M

**Blocking Issues:** None.

**Follow-up Tasks:** WP-07 (Kernel boot orchestration) is the first WP to
drive real components through this lifecycle.

---

### WP-07 — Kernel Boot and Shutdown Orchestration

**Objective:** Implement the `Kernel` interface and the fixed boot/shutdown
phase sequence, wiring together WP-02, WP-03, WP-05, and WP-06, per
[910](910_Phase1_Core_Foundation_Specification.md#core-kernel),
[910](910_Phase1_Core_Foundation_Specification.md#startup-sequence), and
[910](910_Phase1_Core_Foundation_Specification.md#shutdown-sequence).

**Scope:** `Kernel` interface (`start`, `stop`, `getStatus`);
Configuration phase (invokes WP-02); Core Service Init phase (constructs
Service Registry, Event Bus, in that order, per
[910](910_Phase1_Core_Foundation_Specification.md#startup-sequence));
Module Discovery/Init/Start phase driving the Module Lifecycle Manager
(WP-06) over whatever modules are registered at this point (none yet,
beyond the core services themselves — Logging, Storage, Provider, Memory,
Context modules are added in later WPs without changing this orchestration
logic); `KernelReady`, `KernelShuttingDown` events; `kernel.bootTimeoutMs`
and `kernel.shutdownTimeoutMs` configuration; `KernelBootError`.

**Files Expected:** `kernel/` module: `Kernel` implementation, boot phase
sequencing, shutdown phase sequencing.

**Dependencies:** WP-02, WP-03, WP-05, WP-06.

**Public Interfaces:** `Kernel`, `KernelReadyResult`, `KernelStatus`,
`KernelBootError`, `KernelReady` (event), `KernelShuttingDown` (event).

**Acceptance Criteria:**
- `Kernel.start()` with zero additional modules registered completes the
  full phase sequence and resolves with a `KernelReadyResult` listing an
  empty `startedModules` array (or only the core services, per the
  implementer's module-vs-core-service classification — must be
  consistent with WP-08 onward's expectations).
- A `Kernel.start()` call given a config that fails schema validation
  halts with `KernelBootError(phase: "Configuration", ...)` and never
  reaches Core Service Init.
- `Kernel.stop()` emits `KernelShuttingDown` and completes without error
  when no modules are registered.
- Boot exceeding `kernel.bootTimeoutMs` fails with
  `KernelBootError(phase: "Timeout")`.

**Tests Required:** The "Boot test" and "Shutdown test" from
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy),
scoped to zero-module boot/shutdown at this stage (full multi-module boot
is re-verified end-to-end in WP-19).

**Estimated Complexity:** M

**Blocking Issues:** None — all dependencies (WP-02, WP-03, WP-05, WP-06)
precede this WP.

**Follow-up Tasks:** WP-08 through WP-16 each register their component
into this Kernel's Module Discovery step. WP-19 re-verifies the full
end-to-end sequence once every Phase 1 module exists.

---

### WP-08 — Logging Interface

**Objective:** Implement the `Logger`/`LoggerFactory` interface, per
[910](910_Phase1_Core_Foundation_Specification.md#logging-interface).

**Scope:** `Logger` interface (`debug`, `info`, `warn`, `error`);
`LoggerFactory.forModule(moduleId)`; console sink; `logging.level` and
`logging.sinks` configuration (file sink registered here but not yet
functional against real storage — see Blocking Issues); non-throwing
guarantee on sink failure. Registered into the Kernel (WP-07) as a Core
Service Init step, per
[910](910_Phase1_Core_Foundation_Specification.md#startup-sequence).

**Files Expected:** `logging/` module: `Logger`/`LoggerFactory` interfaces
and implementation, console sink.

**Dependencies:** WP-02 (reads `logging.*` config), WP-03 (registers
`LoggerFactory` token), WP-07 (wired into Core Service Init).

**Public Interfaces:** `Logger`, `LoggerFactory`, `LogFields`.

**Acceptance Criteria:**
- `LoggerFactory.forModule("x").info(...)` writes a log line tagged with
  module id `"x"` to the console sink.
- Entries below `logging.level` are discarded at the call site.
- A forced console-sink failure (test double) does not throw back to the
  caller.
- `LoggerFactory` is resolvable via the Service Registry after Kernel
  Core Service Init.

**Tests Required:** Unit tests for level filtering, module tagging,
non-throwing sink-failure behavior; one integration check that Kernel boot
(WP-07) successfully resolves `LoggerFactory`.

**Estimated Complexity:** S

**Blocking Issues:** The file sink (`logging.sinks: ["file"]`) requires
the Storage Interface (WP-10), which is not yet built when this WP lands.
This WP implements the file-sink configuration option but leaves it
unimplemented (console-only) until WP-10 lands; enabling `"file"` before
WP-10 must fail fast with a clear "not yet available" error rather than
silently no-op, so misconfiguration is caught immediately rather than
producing silently dropped logs.

**Follow-up Tasks:** A small follow-up (bundled into WP-10, not a separate
WP) completes the file sink once the Storage Interface exists.

---

### WP-09 — Storage Interface

**Objective:** Implement the `StorageProvider` interface and its
`LocalStorageProvider` implementation, per
[910](910_Phase1_Core_Foundation_Specification.md#storage-interface).

**Scope:** `StorageProvider` interface (`read`, `write`, `query`,
`delete`); `LocalStorageProvider` backed by a local embedded store (concrete
technology chosen by the implementer, per
[070_Storage_Architecture](070_Storage_Architecture.md#future-work));
`storage.local.path` and `storage.local.encryptionKeySource`
configuration; at-rest encryption at this boundary per
[910](910_Phase1_Core_Foundation_Specification.md#storage-interface)'s
Phase 1 Resolution; `StorageIOError`. Registered into the Kernel (WP-07) as
a Core Service Init step.

**Files Expected:** `storage/` module: `StorageProvider` interface,
`LocalStorageProvider` implementation, encryption wrapper, error types.

**Dependencies:** WP-02 (reads `storage.local.*` config), WP-03 (registers
`StorageProvider` token), WP-07 (wired into Core Service Init).

**Public Interfaces:** `StorageProvider`, `QueryCriteria`,
`StorageIOError`.

**Acceptance Criteria:**
- `write(key, value)` followed by `read(key)` returns the written value.
- `read()` on a nonexistent key returns `undefined`, not an error.
- `query()` against `keyPrefix`/`filter`/`limit` returns matching values.
- `delete()` removes a key such that a subsequent `read()` returns
  `undefined`.
- Data at rest is not stored in plaintext (verified by inspecting the
  underlying store directly in a test, per
  [070_Storage_Architecture](070_Storage_Architecture.md#encryption)).
- A forced I/O failure (test double / unwritable path) surfaces as
  `StorageIOError`, and `init()` transitions to `Failed` if the path is
  unwritable at boot.
- Concurrent `write()` calls to the same key do not interleave partial
  writes (per
  [910](910_Phase1_Core_Foundation_Specification.md#thread-safety)).

**Tests Required:** Unit tests for all CRUD paths, encryption-at-rest
verification, I/O failure propagation, and a concurrency test for
same-key writes.

**Estimated Complexity:** M

**Blocking Issues:** None.

**Follow-up Tasks:** Completes WP-08's deferred file sink (bundled here, as
noted in WP-08's Follow-up Tasks). WP-10 adds Event Bus dead-letter
persistence on top of this interface. WP-13 (Memory Manager) depends on
this WP directly.

---

### WP-10 — Event Bus Dead-Letter Persistence

**Objective:** Wire the Event Bus's (WP-05) in-memory dead-letter store to
the Storage Interface (WP-09), per
[910](910_Phase1_Core_Foundation_Specification.md#error-handling-3)'s
Phase 1 Resolution, and complete WP-08's deferred file sink.

**Scope:** Persist dead-lettered events under a reserved key namespace via
`StorageProvider`; expose a query path for inspecting dead-lettered events
(direct `StorageProvider.query()` against that namespace, per
[910](910_Phase1_Core_Foundation_Specification.md#failure-recovery) —
no new public interface method is added, this is a documented key
convention over the existing `StorageProvider.query()`); implement the
Logging Interface's file sink using `StorageProvider`.

**Files Expected:** `events/bus/` module: dead-letter persistence adapter;
`logging/` module: file sink implementation.

**Dependencies:** WP-05, WP-08, WP-09.

**Public Interfaces:** None new — this WP wires existing interfaces
together; the dead-letter key namespace convention is documented but not a
new type.

**Acceptance Criteria:**
- A dead-lettered event survives a process restart (written via
  `StorageProvider`, read back via `StorageProvider.query()` against the
  reserved namespace).
- Enabling `logging.sinks: ["file"]` now succeeds (no longer the "not yet
  available" error from WP-08) and writes log lines to the local store.

**Tests Required:** Integration test: force a handler to exhaust retries,
verify the resulting dead-letter record is queryable via
`StorageProvider.query()`; unit test for the file sink writing and being
readable back.

**Estimated Complexity:** S

**Blocking Issues:** None — both dependencies (WP-05, WP-09) precede this
WP.

**Follow-up Tasks:** None beyond Phase 3's administrative
dead-letter-browsing capability (out of Phase 1 scope, per
[910](910_Phase1_Core_Foundation_Specification.md#failure-recovery)).

---

### WP-11 — Provider Interface

**Objective:** Implement the `AIProvider` interface and `NullAIProvider`,
per
[910](910_Phase1_Core_Foundation_Specification.md#provider-interface).

**Scope:** `AIProvider` interface (`id`, `contextWindow`, `costPerToken`,
`invoke`, `invokeStream`, `healthCheck`); `NullAIProvider` implementation
whose `invoke`/`invokeStream` reject with `ProviderNotImplementedError` and
whose `healthCheck` returns `"Unavailable"`. Registered into the Kernel
(WP-07) during Module Discovery.

**Files Expected:** `providers/` module: `AIProvider` interface,
`NullAIProvider` implementation, error types.

**Dependencies:** WP-03 (registers `AIProvider` token), WP-07 (wired into
Module Discovery).

**Public Interfaces:** `AIProvider`, `ProviderResponse`, `ProviderChunk`,
`ProviderNotImplementedError`.

**Acceptance Criteria:**
- `NullAIProvider.invoke()` and `.invokeStream()` both reject with
  `ProviderNotImplementedError`.
- `NullAIProvider.healthCheck()` resolves to `"Unavailable"`.
- `NullAIProvider` is resolvable via the Service Registry after Kernel
  boot.

**Tests Required:** Unit tests for the three acceptance criteria above.

**Estimated Complexity:** XS

**Blocking Issues:** None.

**Follow-up Tasks:** Phase 2 replaces `NullAIProvider` with real adapters
without changing `AIProvider`, per
[910](910_Phase1_Core_Foundation_Specification.md#future-extension-points-6).

---

### WP-12 — Memory Manager: Working Memory

**Objective:** Implement the Working Memory subset of `MemoryManager`, per
[910](910_Phase1_Core_Foundation_Specification.md#memory-manager) and
[050_Memory_Model](050_Memory_Model.md#working-memory).

**Scope:** `writeWorking`, `readWorking`, `clearWorking`; session-scoped,
bounded storage via `memory.working.maxItemsPerSession` (oldest-eviction on
overflow); backed by the Storage Interface. Long-term memory, retrieval,
and forgetting are explicitly out of scope for this WP (WP-13, WP-14,
WP-15).

**Files Expected:** `memory/` module: `MemoryManager` interface (partial,
extended by later WPs), Working Memory implementation.

**Dependencies:** WP-09 (Storage Interface).

**Public Interfaces:** `MemoryManager` (partial — `writeWorking`,
`readWorking`, `clearWorking`), `WorkingMemoryItem`.

**Acceptance Criteria:**
- `writeWorking` followed by `readWorking` for the same `sessionId`
  returns the written item.
- Writing beyond `memory.working.maxItemsPerSession` evicts the oldest
  item for that session first.
- `clearWorking` empties a session's working memory such that a
  subsequent `readWorking` returns an empty array.
- Working memory for one `sessionId` is unaffected by writes to a
  different `sessionId`.

**Tests Required:** Unit tests for write/read, bound eviction, clear, and
session isolation.

**Estimated Complexity:** S

**Blocking Issues:** None.

**Follow-up Tasks:** WP-13 extends the same `MemoryManager` with
long-term memory methods.

---

### WP-13 — Memory Manager: Long-Term Memory Write Path

**Objective:** Implement `writeLongTerm` for both Semantic and Episodic
memory, per
[910](910_Phase1_Core_Foundation_Specification.md#memory-manager),
[050_Memory_Model](050_Memory_Model.md#semantic-memory), and
[050_Memory_Model](050_Memory_Model.md#episodic-memory).

**Scope:** `writeLongTerm(item)` for `SemanticMemoryItem` and
`EpisodicMemoryItem`; provenance (`source`) and `confidence` fields
persisted on every write; indexing at write time across semantic/keyword/
temporal axes (relationship axis stubbed as a no-op per
[910](910_Phase1_Core_Foundation_Specification.md#responsibilities-4)'s
Phase 1 Resolution); `MemoryItemWritten` event emission; `MemoryWriteError`.
Retrieval (`query`) is explicitly out of scope for this WP (WP-14).

**Files Expected:** `memory/` module: long-term write path, indexing
(semantic/keyword/temporal), `MemoryWriteError`.

**Dependencies:** WP-09 (Storage Interface), WP-05 (Event Bus, to emit
`MemoryItemWritten`), WP-12 (extends the same `MemoryManager` interface).

**Public Interfaces:** `MemoryManager` (extended — `writeLongTerm`),
`LongTermMemoryItem`, `SemanticMemoryItem`, `EpisodicMemoryItem`,
`MemoryWriteError`, `MemoryItemWritten` (event).

**Acceptance Criteria:**
- `writeLongTerm` for a `SemanticMemoryItem` persists `fact`, `entities`,
  `source`, `confidence`, and returns a generated `id`.
- `writeLongTerm` for an `EpisodicMemoryItem` persists `correlationId`,
  `summary`, `source`, `confidence`, and returns a generated `id`.
- Each successful write emits `MemoryItemWritten` with the correct `kind`.
- A forced storage write failure surfaces as `MemoryWriteError`, not a
  generic error and not a silently dropped write.
- The relationship index axis is present in the indexing code path but
  always yields an empty result set (verified by a test asserting the
  no-op behavior explicitly, so the stub is intentional and documented,
  not an oversight).

**Tests Required:** Unit tests for both item kinds' write paths, event
emission, error propagation, and the relationship-axis no-op.

**Estimated Complexity:** M

**Blocking Issues:** None.

**Follow-up Tasks:** WP-14 (Retrieval) reads what this WP writes. Phase 2
replaces the relationship-axis no-op once
[060_Knowledge_Graph](060_Knowledge_Graph.md) exists.

---

### WP-14 — Memory Manager: Retrieval API

**Objective:** Implement `query(context)`, per
[910](910_Phase1_Core_Foundation_Specification.md#memory-manager) and
[050_Memory_Model](050_Memory_Model.md#retrieval).

**Scope:** `query(RetrievalQuery): Promise<RetrievedMemoryResult>` fanning
out across working, semantic, and episodic memory and returning one
merged, ranked result; blended relevance/recency ranking weighted per
memory kind; read-only behavior (`lastAccessedAt` bookkeeping update only);
`MemoryRetrievalError`.

**Files Expected:** `memory/` module: retrieval/ranking logic.

**Dependencies:** WP-12 (Working Memory), WP-13 (Long-Term write path —
retrieval needs data to retrieve against).

**Public Interfaces:** `MemoryManager` (extended — `query`),
`RetrievalQuery`, `RetrievedMemoryResult`, `MemoryRetrievalError`.

**Acceptance Criteria:**
- `query()` against a session with working, semantic, and episodic items
  present returns one merged, ranked result covering all three.
- Ranking reflects the documented weighting (episodic favors recency more
  heavily than semantic, per
  [050_Memory_Model](050_Memory_Model.md#retrieval)) — verified with a
  test fixture where recency and relevance are set up to produce a
  predictable, distinguishable order.
- `query()` never mutates a memory item's persisted content, only
  `lastAccessedAt`.
- A forced storage read failure during `query()` surfaces as
  `MemoryRetrievalError`, never as a silently empty result.

**Tests Required:** Unit tests for fan-out/merge behavior, ranking order,
read-only guarantee, and error propagation, per
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy)
("Storage-backed retrieval test" is the integration-level counterpart,
covered in WP-19).

**Estimated Complexity:** M

**Blocking Issues:** None — both dependencies precede this WP.

**Follow-up Tasks:** WP-16 (Context Manager's Memory Retrieval stage)
calls this WP's `query()` directly.

---

### WP-15 — Memory Manager: Forgetting Strategy

**Objective:** Implement `decay` and `hardDelete`, per
[910](910_Phase1_Core_Foundation_Specification.md#memory-manager) and
[050_Memory_Model](050_Memory_Model.md#forgetting-strategy).

**Scope:** `decay(itemId)` transitioning `status` to `"Archived"` once
`confidence` falls below `memory.decay.thresholdConfidence`; `hardDelete
(itemId)` removing the item and its indexes entirely, emitting
`MemoryItemDeleted`; no-op success (not an error) for `hardDelete` on a
nonexistent `itemId`. Concrete time-based decay curves remain out of scope
(Future Work per `050_Memory_Model.md`, carried forward by
[910](910_Phase1_Core_Foundation_Specification.md#future-extension-points-3)).

**Files Expected:** `memory/` module: decay/delete logic.

**Dependencies:** WP-13 (operates on long-term items written there).

**Public Interfaces:** `MemoryManager` (extended — `decay`, `hardDelete`),
`MemoryItemDeleted` (event).

**Acceptance Criteria:**
- `decay()` on an item below the confidence threshold sets its `status`
  to `"Archived"`; above threshold, `status` remains `"Active"`.
- `hardDelete()` removes the item such that a subsequent `query()` never
  returns it, and emits `MemoryItemDeleted`.
- `hardDelete()` on a nonexistent `itemId` resolves successfully without
  error.

**Tests Required:** Unit tests for both threshold outcomes of `decay()`,
hard-delete removal verified against `query()`, event emission, and the
nonexistent-id no-op case.

**Estimated Complexity:** S

**Blocking Issues:** None.

**Follow-up Tasks:** Concrete decay functions and archival retention
windows remain Future Work, per
[050_Memory_Model](050_Memory_Model.md#future-work) — not a Phase 1 task.

---

### WP-16 — Memory Manager Kernel Registration

**Objective:** Register the completed `MemoryManager` (WP-12 through
WP-15) into the Kernel's Module Discovery/Init/Start sequence.

**Scope:** `MemoryManager` module wrapper conforming to the internal
`Module` interface (WP-06); registration into the Service Registry;
placement in Initialization Order after the Storage Interface, per
[910](910_Phase1_Core_Foundation_Specification.md#initialization-order).
This WP contains no new business logic — it is purely the lifecycle/wiring
seam between a fully-implemented Memory Manager and the Kernel.

**Files Expected:** `memory/` module: `Module`-conforming wrapper;
`kernel/` module: Module Discovery registration entry.

**Dependencies:** WP-07 (Kernel), WP-12, WP-13, WP-14, WP-15 (complete
Memory Manager).

**Public Interfaces:** None new.

**Acceptance Criteria:**
- Kernel boot with the Memory Manager registered reaches `Started` for
  that module and includes it in `KernelReadyResult.startedModules`.
- A forced Storage Interface resolution failure at Memory Manager `init()`
  transitions it to `Failed` and halts boot, per
  [910](910_Phase1_Core_Foundation_Specification.md#lifecycle-3).

**Tests Required:** Integration test: Kernel boot with only Memory
Manager (plus its Storage Interface dependency) registered, verifying
`Started` state and boot-halt-on-failure behavior.

**Estimated Complexity:** XS

**Blocking Issues:** None.

**Follow-up Tasks:** None — this seam pattern (wrapper + registration) is
repeated identically for the Context Manager in WP-18.

---

### WP-17 — Context Manager: Stage Interfaces and Stub Implementations

**Objective:** Implement the four Context Manager stage methods as
interface-complete stubs, per
[910](910_Phase1_Core_Foundation_Specification.md#context-manager).

**Scope:** `ContextManager` interface (`processInput`, `retrieveContext`,
`assemblePrompt`, `postProcessOutput`); `processInput` validating and
normalizing `RawInput` (rejecting malformed input with
`InvalidInputError`); `retrieveContext` calling `MemoryManager.query()`
directly (read-only, synchronous call, not event-driven, per
[910](910_Phase1_Core_Foundation_Specification.md#events-consumed-2));
`assemblePrompt` returning a pass-through `AssembledPrompt` with
`metadata.stub: true`; `postProcessOutput` returning a pass-through
`FinalResult`; `ContextStageCompleted` event emitted after each stage.

**Files Expected:** `context/` module: `ContextManager` interface and stub
implementation, `InvalidInputError`.

**Dependencies:** WP-14 (Memory Manager retrieval, called by
`retrieveContext`), WP-05 (Event Bus, for `ContextStageCompleted`).

**Public Interfaces:** `ContextManager`, `RawInput`, `NormalizedInput`,
`RetrievedContext`, `AssembledPrompt`, `RawModelOutput`, `FinalResult`,
`InvalidInputError`, `ContextStageCompleted` (event).

**Acceptance Criteria:**
- `processInput` rejects input missing both `text` and `attachments`, or
  missing `sessionId`, with `InvalidInputError`.
- A full `processInput → retrieveContext → assemblePrompt →
  postProcessOutput` call sequence emits exactly one
  `ContextStageCompleted` event per stage, in stage order, each carrying
  the same `correlationId`.
- `retrieveContext` calls `MemoryManager.query()` and returns its result
  unmodified as `RetrievedContext`.
- `assemblePrompt`'s output always has `metadata.stub === true`.
- No stage calls anything under the Provider Interface, verified by a
  test double that fails the test if `AIProvider` is invoked.

**Tests Required:** The "Context Manager stub wiring test" from
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy), plus
unit tests for `processInput`'s validation boundary.

**Estimated Complexity:** M

**Blocking Issues:** None — both dependencies precede this WP.

**Follow-up Tasks:** Phase 2 replaces each stub body with live logic
without changing these four method signatures, per
[910](910_Phase1_Core_Foundation_Specification.md#future-extension-points-1).

---

### WP-18 — Context Manager Kernel Registration

**Objective:** Register the completed `ContextManager` (WP-17) into the
Kernel's Module Discovery/Init/Start sequence.

**Scope:** Identical pattern to WP-16, applied to the Context Manager:
`Module`-conforming wrapper, Service Registry registration, placement last
in Initialization Order, per
[910](910_Phase1_Core_Foundation_Specification.md#initialization-order).

**Files Expected:** `context/` module: `Module`-conforming wrapper;
`kernel/` module: Module Discovery registration entry.

**Dependencies:** WP-07 (Kernel), WP-16 (Memory Manager registered — a
declared dependency of Context Manager), WP-17 (complete Context Manager).

**Public Interfaces:** None new.

**Acceptance Criteria:**
- Kernel boot with both Memory Manager and Context Manager registered
  starts them in the order Memory Manager → Context Manager, per
  [910](910_Phase1_Core_Foundation_Specification.md#initialization-order).
- Both modules reach `Started` and appear in `KernelReadyResult
  .startedModules` in that order.

**Tests Required:** Integration test: Kernel boot with Memory Manager and
Context Manager both registered, verifying start order and `Started`
state for both.

**Estimated Complexity:** XS

**Blocking Issues:** None.

**Follow-up Tasks:** WP-19 performs the full nine-component boot this WP's
pattern converges toward.

---

### WP-19 — Full Phase 1 Kernel Wiring

**Objective:** Register every remaining Phase 1 component (Logging,
Storage, Provider) alongside Memory Manager and Context Manager into a
single Kernel boot, completing the Initialization Order in full, per
[910](910_Phase1_Core_Foundation_Specification.md#initialization-order).

**Scope:** Wire Logging Interface (WP-08/WP-10), Storage Interface (WP-09/
WP-10), and Provider Interface (WP-11) into the same Kernel instance
already hosting Memory Manager (WP-16) and Context Manager (WP-18);
verify the complete Startup Sequence and Shutdown Sequence end-to-end, per
[910](910_Phase1_Core_Foundation_Specification.md#startup-sequence) and
[910](910_Phase1_Core_Foundation_Specification.md#shutdown-sequence). No
new component logic is introduced — this WP is pure integration wiring
across everything built in WP-02 through WP-18.

**Files Expected:** `kernel/` module: final Module Discovery ordering and
any remaining wrapper registrations not already added by earlier WPs.

**Dependencies:** WP-08, WP-09, WP-10, WP-11, WP-16, WP-18 (i.e.,
effectively all prior WPs).

**Public Interfaces:** None new.

**Acceptance Criteria:**
- `Kernel.start()` with all nine Phase 1 components registered completes
  the full Initialization Order
  (`Configuration Manager → Service Registry → Event Bus → Logging
  Interface → Storage Interface → Provider Interface → Memory Manager →
  Context Manager`) and reaches `Ready`.
- `Kernel.stop()` reverses that order exactly, per the Shutdown Sequence,
  with no module receiving a call after it has stopped.
- A forced failure in any single module during `start()` halts boot and
  leaves no other module still running, per the "Isolation test" pattern
  from WP-06, now exercised across the full nine-component set.

**Tests Required:** The "Boot test" and "Shutdown test" from
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy), now
run against the full nine-component registration (superseding the
zero-module version from WP-07 and the partial versions from WP-16/WP-18).

**Estimated Complexity:** M

**Blocking Issues:** None — all dependencies precede this WP.

**Follow-up Tasks:** WP-20 adds the remaining cross-cutting integration
tests and confirms the Phase 1 Definition of Done in full.

---

### WP-20 — Phase 1 Integration Test Suite and Definition-of-Done Verification

**Objective:** Add the remaining cross-component integration tests from
[910](910_Phase1_Core_Foundation_Specification.md#testing-strategy) not
already covered by WP-05/WP-17/WP-19, and produce a single verification
pass confirming every item in
[910](910_Phase1_Core_Foundation_Specification.md#definition-of-done).

**Scope:** "Event round-trip test" (if not already fully exercised by
WP-05's unit tests, extend to a true producer/subscriber pair across
module boundaries); "Storage-backed retrieval test" verifying
`MemoryManager.query()` against the real `LocalStorageProvider` (not a
mock) end-to-end; a final checklist pass confirming each of the 11 items
in
[910](910_Phase1_Core_Foundation_Specification.md#definition-of-done),
including verifying that every "Phase 1 Resolution" flagged in `910` is
either still valid or has been reconciled back into its source document.
This WP does not add new production code.

**Files Expected:** A dedicated integration-test module/directory
covering cross-component flows; no changes to component implementation
files.

**Dependencies:** WP-19 (requires the fully wired Kernel).

**Public Interfaces:** None.

**Acceptance Criteria:**
- Every acceptance criterion listed across WP-01 through WP-19 is
  re-confirmed passing in CI as a single suite run (no per-WP regression).
- Every item in
  [910](910_Phase1_Core_Foundation_Specification.md#definition-of-done)
  is explicitly checked off with a link to the test or artifact that
  satisfies it.
- No Phase 1 module imports or depends on any interface owned by `020`
  (beyond the Context Manager stub interfaces), `030`, `060`, `080`
  (beyond the Provider Interface), `090`, `100`, or `110` — verified by a
  dependency/import check across the Phase 1 source tree.

**Tests Required:** The full integration suite described above, run in CI
as the final Phase 1 gate.

**Estimated Complexity:** M

**Blocking Issues:** None — this is the terminal WP of Phase 1.

**Follow-up Tasks:** None within Phase 1. Phase 2 work (per
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-2---ai-layer))
begins only after this WP merges.

---

# Recommended Pull Request Order

1. WP-01 — Repository Scaffolding
2. WP-02 — Configuration Manager
3. WP-03 — Service Registry
4. WP-04 — Event Schema and Types
5. WP-05 — Event Bus Transport
6. WP-06 — Module Lifecycle Manager and Error Boundary
7. WP-07 — Kernel Boot and Shutdown Orchestration
8. WP-08 — Logging Interface
9. WP-09 — Storage Interface
10. WP-10 — Event Bus Dead-Letter Persistence
11. WP-11 — Provider Interface
12. WP-12 — Memory Manager: Working Memory
13. WP-13 — Memory Manager: Long-Term Memory Write Path
14. WP-14 — Memory Manager: Retrieval API
15. WP-15 — Memory Manager: Forgetting Strategy
16. WP-16 — Memory Manager Kernel Registration
17. WP-17 — Context Manager: Stage Interfaces and Stub Implementations
18. WP-18 — Context Manager Kernel Registration
19. WP-19 — Full Phase 1 Kernel Wiring
20. WP-20 — Phase 1 Integration Test Suite and Definition-of-Done
    Verification

This order satisfies every WP's stated dependencies (each WP's
"Dependencies" list contains only WPs earlier in this sequence) and keeps
the repository compiling and passing its test suite after each individual
merge.

---

# Dependency Graph

```
WP-01 (Repository Scaffolding)
  │
  ├── WP-02 (Configuration Manager)
  ├── WP-03 (Service Registry)
  └── WP-04 (Event Schema and Types)
           │
           ▼
       WP-05 (Event Bus Transport)
           │
           ▼
       WP-06 (Module Lifecycle Manager + Error Boundary)
           │
  WP-02 ───┼─── WP-03 ───┘
           ▼
       WP-07 (Kernel Boot / Shutdown Orchestration)
           │
   ┌───────┼────────────────┐
   ▼       ▼                ▼
WP-08   WP-09            WP-11
(Logging) (Storage)     (Provider Interface)
   │       │
   └───┬───┘
       ▼
   WP-10 (Event Bus Dead-Letter Persistence)

WP-09 ──► WP-12 (Memory: Working Memory)
              │
              ▼
          WP-13 (Memory: Long-Term Write) ◄── WP-05, WP-09
              │
              ▼
          WP-14 (Memory: Retrieval API)
              │
              ▼
          WP-15 (Memory: Forgetting Strategy)
              │
              ▼
          WP-16 (Memory Manager Kernel Registration) ◄── WP-07

WP-14 ──► WP-17 (Context Manager Stub) ◄── WP-05
              │
              ▼
          WP-18 (Context Manager Kernel Registration) ◄── WP-07, WP-16

WP-08, WP-09, WP-10, WP-11, WP-16, WP-18
              │
              ▼
          WP-19 (Full Phase 1 Kernel Wiring)
              │
              ▼
          WP-20 (Integration Tests + Definition-of-Done Verification)
```

This is the Phase 1 subset of
[910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#dependency-diagram)'s
component-level Dependency Diagram, expanded to work-package granularity.

---

# Parallel Work Opportunities

Given the graph above, the following WPs have no dependency relationship
to each other and can be implemented concurrently by different
contributors/PRs, provided each still merges only after its own
prerequisites land:

- **After WP-01:** WP-02 (Configuration Manager), WP-03 (Service
  Registry), and WP-04 (Event Schema and Types) can all proceed in
  parallel — none depends on the other two.
- **After WP-07:** WP-08 (Logging Interface), WP-09 (Storage Interface),
  and WP-11 (Provider Interface) can all proceed in parallel — each
  depends only on WP-02/WP-03/WP-07, not on each other.
- **After WP-09:** WP-12 (Memory Manager: Working Memory) can proceed in
  parallel with WP-08's remaining file-sink work and with WP-11 (Provider
  Interface), since none of the three depends on the others.
- **WP-13, WP-14, WP-15** are sequential with respect to each other (each
  extends the same `MemoryManager` interface incrementally and each
  reads/depends on the previous one's data), and are not parallelizable
  among themselves without risking merge conflicts on the same interface
  file — treat this chain as a single contributor's sequential track.
- **WP-16 and WP-17** can proceed in parallel once WP-14 has merged:
  WP-16 only wires the already-complete Memory Manager into the Kernel,
  while WP-17 builds the Context Manager stub against WP-14's `query()` —
  they touch different files (`memory/` wrapper vs. `context/` module) and
  do not depend on each other directly, only on WP-14 and WP-07 in
  common.
- **WP-10** (Event Bus Dead-Letter Persistence) can proceed in parallel
  with the entire WP-12 through WP-17 chain, since it depends only on
  WP-05, WP-08, and WP-09.

WP-18, WP-19, and WP-20 are inherently sequential integration/verification
steps and are not parallelizable — each requires the full set of
components it wires or verifies to already exist.

---

# Definition of Phase 1 Completion

Phase 1 is complete when:

1. WP-01 through WP-20 have all merged in the order given above (or any
   order consistent with the Dependency Graph), each as its own reviewed
   pull request.
2. Every Acceptance Criterion listed under every work package is verified
   passing in CI, culminating in WP-20's single consolidated verification
   pass.
3. Every item in
   [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#definition-of-done)
   is satisfied, which this document's WP-20 exists specifically to
   confirm.
4. Every item in
   [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation)'s
   own Phase 1 Definition of Done is satisfied as a subset of (3) — this
   work breakdown does not relax the Roadmap's exit gate, only refines it
   to work-package granularity.
5. No merged Phase 1 work package introduced a dependency on any
   interface or concrete type owned by an architecture document scheduled
   for Phase 2 or later (`020` beyond the Context Manager stub interfaces,
   `030`, `060`, `080` beyond the Provider Interface, `090`, `100`, `110`),
   per WP-20's dependency/import check.
6. Every **Phase 1 Resolution** noted in
   [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
   has been reviewed at Phase 1 exit: still valid as documented, or
   reconciled back into its source architecture document in the same
   change that altered the resolved behavior, per the Constitution's
   Documentation Policy.
7. [900_Implementation_Roadmap](900_Implementation_Roadmap.md#milestones)'s
   **M1 — Bootable Kernel** milestone is marked reached only once (1)
   through (6) all hold — not on any individual work package's merge.
