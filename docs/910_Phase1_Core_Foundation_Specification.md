# 910_Phase1_Core_Foundation_Specification

Status: Draft

Version: 0.1

Owner: PAIOS

---

## Purpose

This document is the complete implementation specification for **Phase 1 —
Foundation**, as scoped by
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation).
It decomposes Phase 1 into nine concrete, buildable components, each with a
public interface, lifecycle, error-handling contract, event contract,
configuration, and extension points precise enough that an implementer needs
no further architectural decisions to begin work.

This document does not introduce new architecture. It is a Phase-1-scoped
elaboration of [000_Project_Constitution](000_Project_Constitution.md) and
architecture documents `010`, `040`, `050`, `070`, and the Phase-1-relevant
subset of `020` and `080`. Where those documents fully specify a behavior,
this document references them rather than restating them. Where those
documents leave an ambiguity that Phase 1 implementation cannot proceed
without resolving, this document resolves it explicitly and flags the
resolution as **Phase 1 Resolution** so it can be reconciled back into the
source architecture document in a later documentation pass.

Where this document and a referenced architecture document conflict, the
architecture document wins, per
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#purpose)'s own
precedence rule — any such conflict found during implementation must be
raised as a documentation issue, not silently resolved in code.

---

# Scope

In scope:

- The nine Phase 1 components: Core Kernel, Service Registry, Event Bus,
  Context Manager, Memory Manager, Storage Interface, Provider Interface,
  Configuration Manager, Logging Interface.
- Their public interfaces, lifecycles, dependencies, and event contracts, to
  the level of detail needed to implement and unit-test each in isolation.
- The startup sequence, shutdown sequence, dependency ordering, state
  management, thread-safety, and failure-recovery rules that apply across
  all nine components collectively.
- The testing strategy and Definition of Done that gate Phase 1 exit, per
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation).

Out of scope (see referenced documents instead):

- Concrete AI provider adapters, prompt construction, model selection,
  failover, and streaming — owned by
  [080_AI_Router](080_AI_Router.md) and
  [090_Prompt_Builder](090_Prompt_Builder.md), scheduled for Phase 2.
- Concrete Knowledge Graph traversal and embedding generation — owned by
  [060_Knowledge_Graph](060_Knowledge_Graph.md), scheduled for Phase 2.
- Plugin loading, sandboxing, and the Capability Registry — owned by
  [030_Capability_Model](030_Capability_Model.md) and
  [100_Plugin_SDK](100_Plugin_SDK.md), scheduled for Phase 3.
- Workflow orchestration — owned by
  [110_Workflow_Engine](110_Workflow_Engine.md), scheduled for Phase 3.
- User-facing surfaces (CLI, Desktop UI, Settings) and full structured
  observability tooling — scheduled for Phase 4, per
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-4---user-layer).
- Concrete storage backend technology choice, concrete embedded database
  selection — left to implementation within the `StorageProvider` contract
  defined here and in
  [070_Storage_Architecture](070_Storage_Architecture.md).

---

# Objectives

1. Produce a kernel that boots deterministically through a fixed phase
   sequence and reaches a `Ready` state only once every Phase 1 component
   has started successfully, per
   [010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle).
2. Establish the Event Bus as the single in-process transport for all
   inter-component communication, with a versioned event schema, retry
   policy, and dead-letter path, per
   [040_Event_Model](040_Event_Model.md).
3. Establish the Service Registry (DI Container) as the only mechanism by
   which any component obtains a dependency, so every later phase can
   substitute implementations without touching consumer code, per the
   Constitution's Interface-First and Dependency Inversion principles.
4. Stand up the Context Manager as an interface-complete, stub-implemented
   scaffold for the future Context Pipeline, wired to the Event Bus, per
   [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation)'s
   Phase 1 Definition of Done.
5. Stand up the Memory Manager with working, semantic, and episodic memory
   interfaces and a Retrieval API that returns real results against at
   least one working `StorageProvider` implementation.
6. Define the `StorageProvider` and `AIProvider` interfaces completely
   enough that Phase 2 can write concrete adapters against them with zero
   changes to the interfaces themselves.
7. Provide a Configuration Manager that loads, validates, and exposes
   configuration once at boot, and a Logging Interface that every module
   receives at initialization, so that later phases (structured
   cross-component logging in Phase 4, plugin permission logging in Phase
   3) build on a stable foundation rather than retrofitting one.
8. Ensure every Phase 1 component depends only on interfaces defined in
   this document or in `010`/`040`/`050`/`070`/`020`/`080`, and on no
   component outside Phase 1, per the Roadmap's Phase 1 Definition of Done
   ("no component in this phase depends on anything outside it").

---

# Component List

## Core Kernel

### Purpose

The Core Kernel is the boot orchestrator and the container for the other
eight Phase 1 components. It owns exactly the responsibilities enumerated in
[010_Core_Kernel](010_Core_Kernel.md#core-kernel-responsibilities): boot
orchestration, configuration loading (delegated to the Configuration
Manager), dependency injection (delegated to the Service Registry), Event
Bus provisioning, module lifecycle management, and error boundaries. It does
not implement memory, storage, or provider logic itself.

### Responsibilities

- Drive the boot phases in fixed order: Configuration → Core Service Init →
  Module Discovery → Module Init/Start → Ready, per
  [010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle).
- Own the Module Lifecycle Manager and Error Boundary described in
  [010_Core_Kernel](010_Core_Kernel.md#kernel-services).
- Halt boot and report failure if any required module fails to start; never
  continue in an undefined, partially-started state.
- Drive shutdown in reverse dependency order.

### Public Interfaces

```
interface Kernel {
  start(): Promise<KernelReadyResult>
  stop(): Promise<void>
  getStatus(): KernelStatus
}

type KernelReadyResult = {
  startedModules: string[]   // module ids, in start order
  startedAt: string          // ISO 8601 timestamp
}

type KernelStatus = "Booting" | "Ready" | "ShuttingDown" | "Stopped" | "Failed"
```

`Kernel.start()` internally sequences the Configuration Manager, Service
Registry, Event Bus, and the Module Lifecycle Manager described below; none
of those are called by any component other than the Kernel itself during
boot.

### Inputs

- Process-level entry invocation (`Kernel.start()`), with no required
  runtime arguments — all configuration is sourced by the Configuration
  Manager, not passed as start-time arguments, per
  [010_Core_Kernel](010_Core_Kernel.md#configuration).

### Outputs

- A `KernelReadyResult` on successful start, or a rejected promise carrying
  a `KernelBootError` (see Error Handling) on failure.
- A `ModuleStarted` event per started module and a `KernelReady` event on
  the Event Bus once boot completes (see Events Produced).

### Dependencies

- None outside Phase 1. The Kernel is the root of the Phase 1 dependency
  graph (see Dependency Diagram).

### Lifecycle

Follows the Boot Lifecycle exactly as specified in
[010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle). The Kernel itself does
not participate in the `Module` lifecycle state machine below — it is the
component that drives that state machine for every other module, including
the other eight Phase 1 components.

### Error Handling

- A failure during Configuration (invalid/missing required config) halts
  boot with `KernelBootError(phase: "Configuration", cause)`.
- A failure during Module Init/Start halts boot with
  `KernelBootError(phase: "ModuleStart", moduleId, cause)`; already-started
  modules for that boot attempt are stopped in reverse order before the
  error is surfaced, so no boot attempt leaves modules running without a
  Kernel that considers itself `Ready`.
- Per [010_Core_Kernel](010_Core_Kernel.md#error-boundaries), the Kernel
  does not add defensive handling for internal programming errors (e.g. a
  Service Registry lookup for an unregistered interface); those propagate
  as unhandled errors during development and are treated as bugs, not
  runtime cases to guard.

### Events Produced

- `KernelReady` (v1) — payload: `{ startedModules: string[] }`. Emitted once
  after the Ready phase completes.
- `KernelShuttingDown` (v1) — payload: `{}`. Emitted at the start of
  shutdown, before any module is stopped.
- `ModuleFailed` (v1) — payload: `{ moduleId: string, phase: string, error:
  string }`. Emitted when the Error Boundary catches an unrecoverable
  module fault, per [010_Core_Kernel](010_Core_Kernel.md#error-boundaries).

### Events Consumed

- None. The Kernel drives other components imperatively during boot/shutdown
  rather than reacting to events; this is consistent with
  [010_Core_Kernel](010_Core_Kernel.md#event-bus)'s statement that the bus
  is transport, not a substitute for boot orchestration.

### Configuration

- `kernel.bootTimeoutMs` (number, default `30000`) — maximum time allowed
  for the full boot sequence before it is treated as a hung boot and
  reported as a `KernelBootError(phase: "Timeout")`.
- `kernel.shutdownTimeoutMs` (number, default `10000`) — maximum time
  allowed per module during shutdown before that module is force-marked
  `Failed` and shutdown proceeds to the next module.

### Future Extension Points

- Supervised-restart policy per module (flagged as undecided in
  [010_Core_Kernel](010_Core_Kernel.md#future-work)) — not implemented in
  Phase 1; a `Failed` module stays `Failed` until an operator or later-phase
  tooling intervenes.
- Hot-reload semantics for plugins during development — out of scope for
  Phase 1, which only loads the nine built-in Phase 1 components, not
  third-party plugins (plugins arrive in Phase 3).

---

## Service Registry

### Purpose

The Service Registry is the Phase 1 name for
[010_Core_Kernel](010_Core_Kernel.md#dependency-injection)'s DI Container:
the sole mechanism by which any component obtains an implementation of a
dependency, resolved against an interface, never a concrete type.

**Phase 1 Resolution:** `010_Core_Kernel.md` refers to this component as
the "DI Container" throughout. This document uses "Service Registry" as the
Phase 1 implementation name for the same component; the two terms refer to
the same interface and are not separate components. Future documentation
passes should standardize on one term.

### Responsibilities

- Register an implementation against an interface/token, at Kernel Core
  Service Init or Module Init time.
- Resolve a requested interface/token to its registered implementation at
  module construction time.
- Reject resolution of an unregistered interface/token as a programming
  error (not a handled runtime case), per
  [010_Core_Kernel](010_Core_Kernel.md#error-boundaries).
- Support exactly one registered implementation per interface/token at a
  time in Phase 1 (no multi-binding); swapping an implementation means
  re-registering, not resolving a list.

### Public Interfaces

```
interface ServiceRegistry {
  register<T>(token: ServiceToken<T>, factory: () => T): void
  resolve<T>(token: ServiceToken<T>): T
  isRegistered<T>(token: ServiceToken<T>): boolean
}

type ServiceToken<T> = { readonly name: string }  // nominal, phantom-typed
```

`ServiceToken` is a nominal, interface-identifying handle (not a string key
compared by value) so that two unrelated interfaces cannot collide by
sharing a name. Concrete tokens for Phase 1 interfaces (e.g.
`STORAGE_PROVIDER`, `EVENT_BUS`, `CONFIG_MANAGER`, `LOGGER`,
`AI_PROVIDER`) are defined once, alongside their interfaces, and imported
by any module that depends on them.

### Inputs

- `register()` calls made by the Kernel during Core Service Init (for
  kernel services) and by the Module Lifecycle Manager during each
  module's construction (for that module's own exposed interfaces, if any).
- `resolve()` calls made by any module's factory function at construction
  time.

### Outputs

- A constructed instance satisfying the requested interface, or a thrown
  `UnregisteredServiceError` for an unknown token.

### Dependencies

- None. The Service Registry is constructed before any other component
  (see Initialization Order) and depends on nothing else in Phase 1.

### Lifecycle

The Service Registry does not follow the `Module` lifecycle state machine
below — like the Kernel, it is infrastructure the Kernel constructs first,
before Module Discovery begins, since every module's construction requires
it to already exist.

### Error Handling

- `resolve()` on an unregistered token throws `UnregisteredServiceError`
  immediately; this is a programming error, not something callers are
  expected to catch and recover from at runtime, per the Constitution's
  rule against defensive handling of conditions that cannot occur
  internally.
- `register()` called twice for the same token in Phase 1 throws
  `DuplicateRegistrationError` — Phase 1 has no override/replace semantics;
  re-registration support (for testing or hot-swap) is a future extension
  point.

### Events Produced

- None. Registration and resolution are synchronous, direct calls by
  design — this is infrastructure wiring, not a state change the rest of
  the system needs to observe as an event.

### Events Consumed

- None.

### Configuration

- None. The Service Registry has no externally configurable behavior in
  Phase 1.

### Future Extension Points

- Multi-binding (registering more than one implementation per interface,
  e.g. multiple `StorageProvider` tiers as in
  [070_Storage_Architecture](070_Storage_Architecture.md#storage-abstraction))
  is deferred; Phase 1 registers exactly one `StorageProvider` binding.
  Phase 2+ may need named/qualified bindings for Local vs. Cloud vs. Cache
  providers — not required for Phase 1's single-provider Definition of
  Done.
- Scoped registrations (e.g. per-request or per-session lifetimes) are not
  needed until session-scoped Working Memory (see Memory Manager) requires
  it; Phase 1 uses singleton lifetime for all registrations.

---

## Event Bus

### Purpose

The Event Bus is the kernel's single in-process transport for all
event-driven communication, exactly as specified in
[010_Core_Kernel](010_Core_Kernel.md#event-bus), carrying events whose
schema and lifecycle are defined in
[040_Event_Model](040_Event_Model.md).

### Responsibilities

- Accept `emit()` calls from any producer and route them to matching
  subscribers by event `type`, per
  [040_Event_Model](040_Event_Model.md#event-routing).
- Validate every emitted event against its registered schema
  (`type` + `version`) before delivery; reject unregistered or
  schema-invalid events at emission time, per
  [040_Event_Model](040_Event_Model.md#event-schema).
- Deliver events asynchronously, without blocking the producer on
  subscriber completion, per
  [040_Event_Model](040_Event_Model.md#async-execution).
- Apply the retry policy on handler failure and move exhausted events to
  the dead-letter path, per
  [040_Event_Model](040_Event_Model.md#retry) and
  [040_Event_Model](040_Event_Model.md#dead-letter-handling).
- Isolate each subscriber's handler execution behind that subscriber
  module's Error Boundary, per
  [010_Core_Kernel](010_Core_Kernel.md#error-boundaries).

### Public Interfaces

```
interface EventBus {
  emit(event: Event): Promise<EmitResult>
  subscribe<P>(type: string, versions: string[], handler: EventHandler<P>): Subscription
  unsubscribe(subscription: Subscription): void
}

interface EventHandler<P> {
  handle(event: Event<P>): Promise<void>
}

type Event<P = unknown> = {
  id: string
  type: string
  version: string
  timestamp: string
  source: string
  correlationId: string
  payload: P
}

type EmitResult = "Routed" | "Unrouted"
type Subscription = { readonly id: string }
```

Field semantics for `Event` are exactly as defined in
[040_Event_Model](040_Event_Model.md#event-schema); this document does not
redefine them.

### Inputs

- `emit(event)` from any Phase 1 component.
- `subscribe(type, versions, handler)` from any Phase 1 component during
  its own `init()`.

### Outputs

- `EmitResult` synchronously on `emit()` (accepted-onto-bus, not
  handler-completed), per
  [040_Event_Model](040_Event_Model.md#async-execution).
- Asynchronous handler invocations to each matched, version-compatible
  subscriber.
- `EventDeadLettered` (v1) events when an event's retries are exhausted,
  per [040_Event_Model](040_Event_Model.md#dead-letter-handling).

### Dependencies

- None outside Phase 1. Constructed during Core Service Init, before any
  module that subscribes to it exists.

### Lifecycle

The Event Bus does not follow the `Module` lifecycle state machine; it is
core service infrastructure constructed during Core Service Init (see
Initialization Order) and torn down last during shutdown, after every
subscribing module has stopped.

### Error Handling

- An emitted event with an unregistered `type`/`version` or a
  schema-invalid `payload` is rejected synchronously to the producer with
  `InvalidEventError`; it never reaches a subscriber malformed, per
  [040_Event_Model](040_Event_Model.md#event-schema).
- A subscriber handler that throws is caught by that subscriber's module
  Error Boundary and evaluated against the Retry policy in
  [040_Event_Model](040_Event_Model.md#retry) — the Event Bus itself does
  not crash or stop routing to other subscribers.
- Phase 1's dead-letter queue backend is the local `StorageProvider`
  registered via the Storage Interface below (**Phase 1 Resolution**:
  [040_Event_Model](040_Event_Model.md#future-work) leaves the dead-letter
  backend undefined; Phase 1 resolves this by persisting dead-lettered
  events as records through the same `StorageProvider` used for
  everything else, under a reserved key namespace, so no second storage
  mechanism is introduced in Phase 1).

### Events Produced

- `EventDeadLettered` (v1) — payload: `{ originalEvent: Event, attempts:
  number, lastError: string }`, per
  [040_Event_Model](040_Event_Model.md#dead-letter-handling).

### Events Consumed

- None directly by the bus itself; it routes events between other
  components without being a subscriber of anything.

### Configuration

- `eventBus.defaultRetryPolicy` — `{ maxAttempts: number, backoffMs:
  number, backoffMultiplier: number }`, default `{ maxAttempts: 3,
  backoffMs: 500, backoffMultiplier: 2 }`, used for any event type that
  does not declare its own retry policy in its schema registration, per
  [040_Event_Model](040_Event_Model.md#retry) ("there is no single global
  retry count applied blindly to every event" — this default applies only
  when a type-specific policy is absent, it is not itself a global
  override).

### Future Extension Points

- Cross-process/distributed transport, per
  [040_Event_Model](040_Event_Model.md#future-work); Phase 1 is strictly
  in-process, single-instance.
- Ordering guarantees across event types sharing a `correlationId` are
  explicitly deferred by `040_Event_Model.md`; Phase 1 provides no such
  guarantee beyond per-type publish order.

---

## Context Manager

### Purpose

The Context Manager is the Phase 1 scaffold for the future Context
Pipeline described in [020_Context_Pipeline](020_Context_Pipeline.md). Per
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation),
Phase 1 implements the pipeline's stages as **interfaces with stub
implementations, wired to the Event Bus** — not the live Memory Retrieval,
Prompt Assembly, Context Optimization, or Token Management logic, which
depend on components (`060_Knowledge_Graph`, `080_AI_Router`,
`090_Prompt_Builder`) not yet built.

**Phase 1 Resolution:** the Context Pipeline's live logic depends on
`080_AI_Router` (for the token budget, per
[020_Context_Pipeline](020_Context_Pipeline.md#token-management)) and
`060_Knowledge_Graph`, neither of which exists in Phase 1. Phase 1's
Context Manager therefore implements every stage interface below with a
stub body that emits the correct stage-boundary event and passes its input
through unchanged (Input Processing, Memory Retrieval, Prompt Assembly) or
returns a fixed placeholder-free pass-through result (Output
Post-Processing), so the Event Bus wiring, stage sequencing, and interface
shapes are all real and testable, while the content-level logic is
deferred to Phase 2 exactly as the Roadmap specifies.

### Responsibilities

- Expose one interface method per Context Pipeline stage
  (`processInput`, `retrieveContext`, `assemblePrompt`,
  `postProcessOutput`), matching the stage boundaries in
  [020_Context_Pipeline](020_Context_Pipeline.md#context-lifecycle).
- Emit a stage-boundary event after each stage completes, so downstream
  Phase 2 logic (and any Phase 1 subscriber, such as the Logging
  Interface) can observe the pipeline's shape before it does anything
  substantive.
- Call into the Memory Manager's Retrieval API for the `retrieveContext`
  stage (read-only), even though Phase 1's Memory Manager itself may only
  return results from a single working `StorageProvider` implementation.
- Never call an AI provider directly; `assemblePrompt` in Phase 1 returns a
  provider-agnostic stub prompt structure without invoking anything under
  the Provider Interface — that invocation is a Phase 2 concern owned by
  [080_AI_Router](080_AI_Router.md).

### Public Interfaces

```
interface ContextManager {
  processInput(raw: RawInput): Promise<NormalizedInput>
  retrieveContext(input: NormalizedInput): Promise<RetrievedContext>
  assemblePrompt(input: NormalizedInput, context: RetrievedContext): Promise<AssembledPrompt>
  postProcessOutput(prompt: AssembledPrompt, rawOutput: RawModelOutput): Promise<FinalResult>
}

type RawInput = { text: string, attachments?: unknown[], sessionId: string, source: string }
type NormalizedInput = { text: string, sessionId: string, source: string, receivedAt: string }
type RetrievedContext = { items: MemoryItem[] }   // MemoryItem defined by Memory Manager
type AssembledPrompt = { representation: unknown, metadata: { stub: true } }
type RawModelOutput = { text: string }
type FinalResult = { text: string, sessionId: string }
```

Phase 1's `AssembledPrompt.metadata.stub` is always `true`, signaling to any
consumer that this is not a real, budget-fitted prompt — Phase 2 removes
this field once Token Management and Prompt Builder are live.

### Inputs

- `RawInput` from whatever caller invokes the pipeline (in Phase 1, this is
  exercised only by unit/integration tests, since no CLI or Desktop UI
  exists until Phase 4).

### Outputs

- `FinalResult`, plus one stage-boundary event per stage on the Event Bus.

### Dependencies

- Event Bus (to emit stage-boundary events).
- Memory Manager (for `retrieveContext`, read-only).
- Service Registry (to resolve the above at construction time).
- Does **not** depend on the Provider Interface or Configuration Manager
  directly in Phase 1's stub form; a future Phase 2 revision will add a
  Provider Interface dependency to `assemblePrompt`'s real implementation.

### Lifecycle

Follows the standard `Module` lifecycle (see State Management) like any
other Phase 1 component: `Discovered → Initialized → Started → Stopped |
Unloaded`, with `Failed` on unrecoverable init/start error.

### Error Handling

- `processInput` rejects malformed `RawInput` (missing `text` and no
  `attachments`, missing `sessionId`) with `InvalidInputError` at this
  boundary, per
  [020_Context_Pipeline](020_Context_Pipeline.md#input-processing) —
  later stages assume their input already passed this check.
- `retrieveContext`, `assemblePrompt`, and `postProcessOutput` do not
  perform additional input validation beyond type-shape checks; per the
  Constitution, once Input Processing has validated a request, downstream
  stages do not re-guard against conditions Input Processing already
  ruled out.
- Any stage's stub implementation encountering a genuine failure (e.g. the
  Memory Manager call in `retrieveContext` fails) surfaces the error to
  the caller rather than silently returning an empty result; a stub is
  simplified in logic, not in error transparency.

### Events Produced

- `ContextStageCompleted` (v1) — payload: `{ stage: "InputProcessing" |
  "MemoryRetrieval" | "PromptAssembly" | "OutputPostProcessing",
  correlationId: string }`. Emitted once per stage, after that stage's
  method returns successfully.

### Events Consumed

- None in Phase 1. The stub implementation calls the Memory Manager
  directly (a request/response call, not an event) because Retrieval is
  read-only and needs a synchronous result, consistent with
  [050_Memory_Model](050_Memory_Model.md#retrieval) treating retrieval as
  a direct query API rather than an event-driven flow.

### Configuration

- None specific to the Context Manager in Phase 1; its stub behavior is
  fixed and not configurable, to avoid speculative configuration ahead of
  Phase 2's real logic (KISS).

### Future Extension Points

- Phase 2 replaces each stub method body with live logic (Context
  Optimization, Token Management via the Provider Interface, live
  Knowledge Graph queries) without changing the four method signatures
  above, per the Interface-First principle — this is the explicit purpose
  of freezing the interface in Phase 1.
- Streaming output support, flagged as Future Work in
  [020_Context_Pipeline](020_Context_Pipeline.md#future-work), is not
  present in Phase 1's `postProcessOutput` signature.

---

## Memory Manager

### Purpose

The Memory Manager implements the Phase-1-required subset of
[050_Memory_Model](050_Memory_Model.md): Working, Semantic, and Episodic
memory interfaces and the Retrieval API, backed by the Storage Interface
below. Per the Roadmap's Phase 1 Definition of Done, it must return real
results against at least one working `StorageProvider` implementation —
unlike the Context Manager, the Memory Manager is not a stub in Phase 1.

### Responsibilities

- Implement Working Memory: session-scoped, bounded storage read/written
  by the Context Manager, per
  [050_Memory_Model](050_Memory_Model.md#working-memory).
- Implement Long-Term Memory's two shapes, Semantic and Episodic, per
  [050_Memory_Model](050_Memory_Model.md#semantic-memory) and
  [050_Memory_Model](050_Memory_Model.md#episodic-memory), including
  provenance (`source`) and `confidence` on every long-term item.
- Implement the Retrieval API (`query(context)`) that fans out across
  working, semantic, and episodic memory and returns one merged, ranked
  result, per
  [050_Memory_Model](050_Memory_Model.md#retrieval).
- Implement indexing at write time (semantic/embedding, keyword,
  relationship, temporal axes), per
  [050_Memory_Model](050_Memory_Model.md#memory-indexing).
  **Phase 1 Resolution:** the relationship (graph) index axis requires
  [060_Knowledge_Graph](060_Knowledge_Graph.md), which does not exist in
  Phase 1. Phase 1 implements the semantic, keyword, and temporal index
  axes fully, and the relationship axis as a no-op that always returns an
  empty result set — this keeps the four-axis interface shape stable for
  Phase 2 without requiring a graph implementation now.
- Implement the Forgetting Strategy's confidence decay and explicit hard
  deletion, per
  [050_Memory_Model](050_Memory_Model.md#forgetting-strategy). Archival
  (as distinct from hard delete) is implemented as a status flag on the
  item, without a separate archive store, in Phase 1.

### Public Interfaces

```
interface MemoryManager {
  writeWorking(sessionId: string, item: WorkingMemoryItem): Promise<void>
  readWorking(sessionId: string): Promise<WorkingMemoryItem[]>
  clearWorking(sessionId: string): Promise<void>

  writeLongTerm(item: SemanticMemoryItem | EpisodicMemoryItem): Promise<string>  // returns id
  query(context: RetrievalQuery): Promise<RetrievedMemoryResult>

  decay(itemId: string): Promise<void>
  hardDelete(itemId: string): Promise<void>
}

type WorkingMemoryItem = { key: string, value: unknown, writtenAt: string }

type LongTermMemoryItem = {
  id: string
  createdAt: string
  lastAccessedAt: string
  source: string
  confidence: number
  status: "Active" | "Archived"
}
type SemanticMemoryItem = LongTermMemoryItem & { kind: "Semantic", fact: string, entities: string[] }
type EpisodicMemoryItem = LongTermMemoryItem & { kind: "Episodic", correlationId: string, summary: string }

type RetrievalQuery = { sessionId: string, text: string, limit: number }
type RetrievedMemoryResult = { items: (WorkingMemoryItem | SemanticMemoryItem | EpisodicMemoryItem)[], rankedIds: string[] }
```

This is the formal `MemoryAPI` interface that
[050_Memory_Model](050_Memory_Model.md#retrieval) refers to in prose
without a signature; this document is the authoritative source for that
signature until `050_Memory_Model.md` is amended to include it directly.

### Inputs

- `writeWorking`/`readWorking`/`clearWorking` from the Context Manager's
  Input Processing and Output Post-Processing stub stages.
- `writeLongTerm` from the Context Manager's Output Post-Processing stage,
  or a future capability invocation (Phase 3+).
- `query` from the Context Manager's `retrieveContext` stage.

### Outputs

- `RetrievedMemoryResult`, ranked per
  [050_Memory_Model](050_Memory_Model.md#retrieval)'s blended
  relevance/recency rule, weighted per memory kind.
- Persisted items via the Storage Interface, each indexed on write per
  Memory Indexing above.

### Dependencies

- Storage Interface (all reads/writes go through `StorageProvider`; the
  Memory Manager holds no direct database or file handle).
- Event Bus (to emit memory-write events, see Events Produced).
- Service Registry (to resolve the Storage Interface at construction).

### Lifecycle

Standard `Module` lifecycle. `Started` state requires a successfully
resolved `StorageProvider`; if resolution fails, the Memory Manager
transitions to `Failed` during `init()`, per
[010_Core_Kernel](010_Core_Kernel.md#module-lifecycle).

### Error Handling

- A `query()` call is read-only and never mutates memory beyond
  `lastAccessedAt` bookkeeping, per
  [050_Memory_Model](050_Memory_Model.md#retrieval); a storage read
  failure during `query()` propagates as `MemoryRetrievalError` rather
  than silently returning an empty result, so callers cannot mistake a
  failure for "no relevant memory."
- `writeLongTerm` failures (a storage write failure, a schema-invalid
  item) propagate as `MemoryWriteError`; Output Post-Processing (Context
  Manager) is responsible for deciding how to surface that to its own
  caller, per
  [020_Context_Pipeline](020_Context_Pipeline.md#output-post-processing).
- `hardDelete` on a nonexistent `itemId` is a no-op success, not an error —
  deleting something already gone satisfies the caller's intent.

### Events Produced

- `MemoryItemWritten` (v1) — payload: `{ itemId: string, kind: "Working" |
  "Semantic" | "Episodic" }`. Emitted after every successful write.
- `MemoryItemDeleted` (v1) — payload: `{ itemId: string }`. Emitted after
  `hardDelete`.

### Events Consumed

- None in Phase 1. Memory writes happen through direct calls from the
  Context Manager, not by subscribing to pipeline events — this keeps
  write ordering explicit and matches
  [050_Memory_Model](050_Memory_Model.md#long-term-memory)'s rule that
  writes happen only through Output Post-Processing or an explicit
  capability invocation, never as an incidental side effect of an
  unrelated event.

### Configuration

- `memory.working.maxItemsPerSession` (number, default `50`) — bounds
  Working Memory per
  [050_Memory_Model](050_Memory_Model.md#working-memory)'s requirement
  that it not accumulate unbounded history. Exceeding the bound evicts the
  oldest item first.
- `memory.decay.thresholdConfidence` (number, default `0.2`) — the
  confidence value below which `decay()` transitions an item's `status` to
  `"Archived"`, per
  [050_Memory_Model](050_Memory_Model.md#forgetting-strategy). Concrete
  decay functions remain Future Work per `050_Memory_Model.md`; Phase 1
  only implements the threshold check, not a time-based decay curve.

### Future Extension Points

- Relationship-axis indexing becomes real once
  [060_Knowledge_Graph](060_Knowledge_Graph.md) is implemented in Phase 2;
  the `query()` signature does not change.
- Confidence-decay functions, promotion criteria from Working to Long-Term
  Memory, and archival retention windows are explicitly Future Work in
  [050_Memory_Model](050_Memory_Model.md#future-work) and remain
  unimplemented beyond the fixed threshold check above.

---

## Storage Interface

### Purpose

The Storage Interface is the Phase 1 name for the `StorageProvider`
abstraction defined in
[070_Storage_Architecture](070_Storage_Architecture.md#storage-abstraction).
It is the sole path through which any Phase 1 component persists or reads
data.

### Responsibilities

- Provide `read`, `write`, `query`, and `delete` against a key/criteria
  model, per
  [070_Storage_Architecture](070_Storage_Architecture.md#storage-abstraction).
- Guarantee that no provider-specific type crosses this boundary; the
  Phase 1 `LocalStorageProvider` implementation translates to and from
  PAIOS-native types only.
- Serve as the authoritative local store for Working Memory, Long-Term
  Memory, and Configuration, per
  [070_Storage_Architecture](070_Storage_Architecture.md#local-storage).
- Perform encryption at rest transparently at this boundary, per
  [070_Storage_Architecture](070_Storage_Architecture.md#encryption).
  **Phase 1 Resolution:** `070_Storage_Architecture.md` leaves key
  management/recovery UX as Future Work; Phase 1 requires the
  `LocalStorageProvider` to encrypt at rest using a key sourced from a
  single local configuration-provided secret (see Configuration below),
  with user-facing key management UX deferred to the Phase 4 Settings
  surface. This satisfies "encrypted at rest" as a property without
  requiring the full key-recovery UX ahead of Phase 4.

### Public Interfaces

```
interface StorageProvider {
  read(key: string): Promise<unknown | undefined>
  write(key: string, value: unknown): Promise<void>
  query(criteria: QueryCriteria): Promise<unknown[]>
  delete(key: string): Promise<void>
}

type QueryCriteria = { keyPrefix?: string, filter?: Record<string, unknown>, limit?: number }
```

Phase 1 registers exactly one `StorageProvider` implementation
(`LocalStorageProvider`) against this interface in the Service Registry,
satisfying the Roadmap's Phase 1 requirement of "at least one working
implementation." Cloud and Cache tiers remain Future Work beyond Phase 1
(they are not scheduled by name in any phase of
[900_Implementation_Roadmap](900_Implementation_Roadmap.md), and are noted
here only as Future Extension Points).

### Inputs

- `read`/`write`/`query`/`delete` calls from the Memory Manager, the
  Configuration Manager, and the Event Bus's dead-letter path.

### Outputs

- The requested value(s), or `undefined`/empty array for a miss, per
  standard key-value/query semantics; a miss is not an error.

### Dependencies

- None outside Phase 1. `LocalStorageProvider` owns its embedded storage
  technology internally; that technology choice is implementation detail
  not fixed by this document, per
  [070_Storage_Architecture](070_Storage_Architecture.md#future-work).

### Lifecycle

Standard `Module` lifecycle. `init()` opens/creates the local embedded
store and fails to `Failed` if it cannot be opened (e.g. filesystem
permission error) — this is treated as a boundary error per the
Constitution's rule that I/O failures are handled at boundaries.

### Error Handling

- `read`/`write`/`query`/`delete` failures due to underlying I/O (disk
  full, permission denied, corruption) propagate as `StorageIOError`,
  caught by the calling module's Error Boundary; the Storage Interface
  itself does not retry internally — retry, if appropriate, is the
  caller's decision (e.g. the Memory Manager may retry a transient write
  failure, per its own policy, rather than the Storage Interface silently
  retrying underneath it).
- A read for a nonexistent key returns `undefined`, not an error.

### Events Produced

- None. Storage operations are synchronous request/response calls, not
  events, consistent with
  [070_Storage_Architecture](070_Storage_Architecture.md) describing reads
  and writes as direct interface calls.

### Events Consumed

- None.

### Configuration

- `storage.local.path` (string, required) — filesystem path (or
  platform-equivalent) for the local embedded store.
- `storage.local.encryptionKeySource` (string, default
  `"local-config-secret"`) — identifies where the at-rest encryption key
  is sourced from in Phase 1, per the Phase 1 Resolution above.

### Future Extension Points

- `CloudStorageProvider` and `CacheProvider` (per
  [070_Storage_Architecture](070_Storage_Architecture.md#cloud-storage)
  and
  [070_Storage_Architecture](070_Storage_Architecture.md#cache)) are
  additional `StorageProvider` implementations addable without changing
  this interface or any Phase 1 consumer, per Provider Independence.
- Migration and Backup capabilities, per
  [070_Storage_Architecture](070_Storage_Architecture.md#migration) and
  [070_Storage_Architecture](070_Storage_Architecture.md#backup), operate
  against this same interface and are scheduled once the Capability Model
  exists (Phase 3).

---

## Provider Interface

### Purpose

The Provider Interface is the Phase 1 definition of the `AIProvider`
abstraction from [080_AI_Router](080_AI_Router.md#provider-abstraction).
Per the Constitution's Interface-First principle and per
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation)'s
requirement that no component may be implemented ahead of the components it
depends on, Phase 1 freezes this interface's shape so that Phase 2's
concrete Provider Adapters and AI Router logic can be built against it
without changing the contract. Phase 1 does not implement routing, model
selection, cost optimization, or failover — those are Phase 2 concerns
owned by `080_AI_Router.md`.

**Phase 1 Resolution:** the Roadmap does not list "Provider Interface" as
an explicit Phase 1 deliverable by name, but Context Manager's future
Token Management logic and the general Interface-First principle require
this interface to exist and be stable before Phase 2 begins. Phase 1
therefore defines the interface and registers exactly one
`NullAIProvider` implementation (below) purely to satisfy the Service
Registry's single-binding requirement and to make the interface
exercisable by unit tests; `NullAIProvider` performs no real invocation and
must not be mistaken for a Phase 2 Provider Adapter.

### Responsibilities

- Define `id`, `contextWindow`, `costPerToken`, `invoke`, `invokeStream`,
  and `healthCheck` exactly as specified in
  [080_AI_Router](080_AI_Router.md#provider-abstraction).
- Guarantee that no vendor SDK type crosses this boundary, per the
  Constitution's Provider Independent principle.
- Provide a `NullAIProvider` Phase 1 implementation whose `invoke()` and
  `invokeStream()` reject with `ProviderNotImplementedError` and whose
  `healthCheck()` always returns `"Unavailable"` — this is a placeholder
  registration, not a functioning provider, and Phase 1 does not claim to
  produce real AI responses (per this document's Scope).

### Public Interfaces

```
interface AIProvider {
  readonly id: string
  readonly contextWindow: number
  readonly costPerToken: { input: number, output: number }
  invoke(prompt: AssembledPrompt): Promise<ProviderResponse>
  invokeStream(prompt: AssembledPrompt): AsyncIterable<ProviderChunk>
  healthCheck(): Promise<"Available" | "Degraded" | "Unavailable">
}

type ProviderResponse = { text: string, tokensUsed: number }
type ProviderChunk = { text: string, done: boolean }
```

`AssembledPrompt` is the same type produced by the Context Manager's
`assemblePrompt`, per
[080_AI_Router](080_AI_Router.md#provider-abstraction)'s statement that the
Context Pipeline's assembled prompt is the router's only accepted input.

### Inputs

- None in Phase 1 beyond what `NullAIProvider` receives and immediately
  rejects; no Phase 1 component calls `invoke`/`invokeStream` expecting a
  real result.

### Outputs

- A rejected promise from `NullAIProvider.invoke()`/`invokeStream()` in
  Phase 1; `healthCheck()` returns `"Unavailable"`.

### Dependencies

- None. Registered in the Service Registry during Core Service Init,
  available for resolution but not invoked by any Phase 1 workflow.

### Lifecycle

Standard `Module` lifecycle for the registration wrapper; `NullAIProvider`
has no meaningful `Started` behavior beyond being resolvable.

### Error Handling

- `invoke()`/`invokeStream()` on `NullAIProvider` always reject with
  `ProviderNotImplementedError` — this is expected, tested behavior in
  Phase 1, not a fault to be caught by an Error Boundary; any Phase 1 code
  path that calls it in a non-test context is a scoping bug, since Phase 1
  has no caller that should invoke a real provider.

### Events Produced

- None.

### Events Consumed

- None.

### Configuration

- None. `NullAIProvider` takes no configuration.

### Future Extension Points

- Phase 2 registers one or more real `AIProvider` implementations (e.g.
  `ProviderAdapterA`) in place of `NullAIProvider`, and builds
  [080_AI_Router](080_AI_Router.md)'s Model Selection, Cost Optimization,
  Routing, Failover, and Retry Policy logic on top of this unchanged
  interface.
- `costPerToken`'s per-token input/output split and `contextWindow` become
  load-bearing once Context Manager's Token Management logic (Phase 2)
  computes a real budget from them, per
  [020_Context_Pipeline](020_Context_Pipeline.md#token-management).

---

## Configuration Manager

### Purpose

The Configuration Manager is the Phase 1 name for
[010_Core_Kernel](010_Core_Kernel.md#configuration)'s Configuration
Service: the sole path by which any module reads configuration.

### Responsibilities

- Load configuration from defined sources (file, environment, defaults) in
  a fixed precedence order, merge them, and validate the merged result
  against a schema before Core Service Init completes, per
  [010_Core_Kernel](010_Core_Kernel.md#configuration).
- Halt boot if validation fails, per
  [010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle) Phase 1
  (Configuration).
- Expose configuration read-only after boot; no module mutates loaded
  configuration at runtime in Phase 1.

### Public Interfaces

```
interface ConfigurationManager {
  get<T>(key: string, defaultValue?: T): T
  getRequired<T>(key: string): T
  isLoaded(): boolean
}
```

This is the formal `ConfigService` interface that
[010_Core_Kernel](010_Core_Kernel.md#configuration) refers to in prose
without a signature; this document is the authoritative source for that
signature until `010_Core_Kernel.md` is amended to include it directly.

### Inputs

- Configuration file path(s), environment variables, and compiled-in
  defaults, merged in that precedence order (file overrides defaults;
  environment overrides file — **Phase 1 Resolution:** precedence order is
  not specified in `010_Core_Kernel.md`; this document fixes it as
  `defaults < file < environment`, highest-precedence last, the
  conventional order for twelve-factor-style configuration, so
  implementation has an unambiguous rule to follow).

### Outputs

- Typed configuration values via `get`/`getRequired`, to any module that
  resolves `ConfigurationManager` from the Service Registry.

### Dependencies

- None outside Phase 1. Loaded and validated first, during the
  Configuration boot phase, before the Service Registry registers any
  other kernel service that depends on config values (e.g.
  `storage.local.path`).

### Lifecycle

Not a `Module` in the standard lifecycle sense — it is constructed and
fully loaded during the Kernel's Configuration boot phase, before Module
Discovery begins, since every other module's `init()` may need to read
configuration.

### Error Handling

- Schema-invalid or missing required configuration halts boot with
  `ConfigurationError(key, reason)`; per
  [010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle), no service starts
  on unvalidated configuration.
- `getRequired()` called for a key that passed schema validation always
  succeeds; calling it for a key not covered by the schema is a
  programming error (`UnknownConfigKeyError`), not a runtime case to
  guard defensively.

### Events Produced

- None. Configuration is read-only after boot in Phase 1; there is no
  runtime configuration-change event because there is no runtime
  configuration-change mechanism yet (`010_Core_Kernel.md` explicitly
  defers that to "explicit, event-driven mechanisms," which Phase 4's
  Settings surface introduces).

### Events Consumed

- None.

### Configuration

- N/A — the Configuration Manager configures itself via its own load
  sources (file path convention, environment variable prefix), fixed at
  `paios.config.json` for file source and a `PAIOS_` environment variable
  prefix in Phase 1 (**Phase 1 Resolution**: neither is specified in
  `010_Core_Kernel.md`; fixed here for implementation to proceed).

### Future Extension Points

- Phase 4's Settings surface introduces runtime configuration changes,
  observable by CLI/Desktop UI "without restart, where the Kernel's
  lifecycle model allows it," per
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-4---user-layer)
  — this requires an explicit, event-driven configuration-change
  mechanism not built in Phase 1.

---

## Logging Interface

### Purpose

The Logging Interface provides the minimal, structured logging contract
that [010_Core_Kernel](010_Core_Kernel.md#module-lifecycle) already assumes
exists when it states a module is given "its context (configuration,
Event Bus handle, logger)" at `init()`. Full cross-component, end-to-end
traceable logging for CLI/Desktop UI consumption is a Phase 4 deliverable,
per
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-4---user-layer);
Phase 1 builds the interface and a minimal local implementation so that
every Phase 1 component has something concrete to log through from the
start, rather than retrofitting a logging call site into eight already-built
components later.

**Phase 1 Resolution:** no `0XX` architecture document defines a logging
interface (flagged as a gap in
[901_Architecture_Audit_Report](901_Architecture_Audit_Report.md#major-issues)).
This document resolves that gap for Phase 1's purposes only; a dedicated
Logging architecture document remains required before Phase 4, per the
Roadmap's own Risks section, and should supersede this section's interface
if it changes it.

### Responsibilities

- Provide leveled log emission (`debug`, `info`, `warn`, `error`) tagged
  with the emitting module's id and, where available, a `correlationId`
  matching the Event Model's field of the same name, per
  [040_Event_Model](040_Event_Model.md#event-schema), so a later phase can
  join log lines to their originating event chain.
- Write log entries to a local sink (console and/or local file via the
  Storage Interface) in Phase 1; no remote log shipping.
- Never throw from a logging call — a logging failure must not take down
  the module that attempted to log, per the Constitution's error-boundary
  principle applied to a non-critical-path concern.

### Public Interfaces

```
interface Logger {
  debug(message: string, fields?: LogFields): void
  info(message: string, fields?: LogFields): void
  warn(message: string, fields?: LogFields): void
  error(message: string, fields?: LogFields): void
}

type LogFields = { correlationId?: string, [key: string]: unknown }
```

Each module receives a `Logger` instance pre-tagged with its own module id
(via a factory `LoggerFactory.forModule(moduleId): Logger`, resolved once
per module at `init()` through the Service Registry) so call sites never
pass their own module id manually.

### Inputs

- `debug`/`info`/`warn`/`error` calls from any Phase 1 module, at any point
  in its lifecycle.

### Outputs

- Structured log lines written to the configured sink(s); no return value.

### Dependencies

- Storage Interface, only if the local file sink is enabled (see
  Configuration); the console sink has no dependency.
- Service Registry (to resolve `LoggerFactory` at construction).

### Lifecycle

Constructed during Core Service Init, before Module Discovery, so it is
available to every module's `init(context)` call, per
[010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle).

### Error Handling

- An internal sink failure (e.g. disk full for the file sink) is caught
  internally and does not propagate to the calling module; the Logging
  Interface falls back to the console sink for that entry and continues,
  since a broken log sink must never become the reason a module fails to
  start or operate.

### Events Produced

- None. Logging is a direct, synchronous call, not routed through the
  Event Bus, so that logging remains available even if the Event Bus
  itself is the thing failing.

### Events Consumed

- None directly, though in Phase 1 the Context Manager's
  `ContextStageCompleted` event (see Context Manager) is, by convention,
  also logged by a Phase 1 diagnostic subscriber for local visibility
  during development — this subscriber is optional tooling, not a
  required Phase 1 component.

### Configuration

- `logging.level` (string enum: `"debug" | "info" | "warn" | "error"`,
  default `"info"`) — entries below this level are discarded at the call
  site, not written and filtered later.
- `logging.sinks` (array of `"console" | "file"`, default `["console"]`) —
  which sink(s) receive log entries.

### Future Extension Points

- Phase 4 extends this into full structured, cross-component traceable
  logging across Kernel, Event Model, and AI Router, per the Roadmap's
  Phase 4 Definition of Done, and is expected to be the trigger for
  authoring the dedicated Logging architecture document referenced above.
- Remote log shipping / observability backend integration is not part of
  Phase 1 or Phase 4 per any current roadmap phase; noted here only as a
  plausible future need.

---

# Startup Sequence

The startup sequence is the Phase 1 realization of
[010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle), naming exactly which
of the nine Phase 1 components is constructed at each boot phase:

1. **Configuration** — the Configuration Manager loads and validates all
   configuration (`kernel.*`, `storage.*`, `memory.*`, `logging.*`) before
   anything else runs. Boot halts here on validation failure.
2. **Core Service Init** — in this fixed order: Service Registry →
   Event Bus → Logging Interface → Storage Interface → Configuration
   Manager is registered into the Service Registry (it was already loaded
   in step 1, and is now made resolvable for other modules). The Storage
   Interface's `init()` opens the local embedded store, using
   `storage.local.path` from the Configuration Manager. The Logging
   Interface's `init()` resolves the Storage Interface only if the file
   sink is enabled.
3. **Module Discovery** — the remaining Phase 1 modules are enumerated in
   dependency order: Memory Manager (depends on Storage Interface) →
   Provider Interface / `NullAIProvider` (no dependencies) → Context
   Manager (depends on Memory Manager, Event Bus).
4. **Module Init/Start** — each discovered module is constructed via the
   Service Registry, `init(context)` is called (context includes
   configuration values it declared, an Event Bus handle, and a tagged
   `Logger`), then `start()`. A `ModuleStarted` event is emitted on the
   Event Bus per module. A module failing `init()` or `start()` halts
   boot per Error Handling in Core Kernel above.
5. **Ready** — once every Phase 1 module has reached `Started`, the Kernel
   emits `KernelReady` and `Kernel.start()`'s returned promise resolves
   with the list of started module ids.

---

# Shutdown Sequence

Shutdown reverses the Startup Sequence's dependency order, per
[010_Core_Kernel](010_Core_Kernel.md#boot-lifecycle):

1. The Kernel emits `KernelShuttingDown`.
2. Modules are stopped dependents-first: Context Manager → Provider
   Interface → Memory Manager (mirroring reverse Module Discovery order
   from Startup step 3).
3. Core services are torn down last, in reverse of Core Service Init:
   Storage Interface → Logging Interface → Event Bus → Service Registry.
   The Storage Interface is stopped only after the Memory Manager (its
   only Phase 1 consumer besides the optional Logging file sink) has
   already stopped, so no module attempts a storage call after the
   Storage Interface has closed its store.
4. Configuration is not "torn down" — it was read-only after boot and is
   simply released when the process exits.

Each module's `stop()` is bounded by `kernel.shutdownTimeoutMs` (see Core
Kernel Configuration); a module that does not stop within that window is
force-marked `Failed` and shutdown proceeds to the next module rather than
hanging indefinitely.

---

# Dependency Diagram

```
Configuration Manager (loaded first, no dependencies)
        │
        ▼
Service Registry (no dependencies)
        │
        ▼
Event Bus (no dependencies)
        │
        ├──────────────┬───────────────┐
        ▼              ▼               ▼
Logging Interface   Storage Interface   Provider Interface
        │              │             (no dependencies;
        │ (optional     │              registers NullAIProvider)
        │  file sink)   │
        │              ▼
        │        Memory Manager
        │              │
        └──────────────┼───────────────┐
                        ▼               │
                Context Manager ◄───────┘
             (Memory Manager, Event Bus)
```

Notes:

- Configuration Manager, Service Registry, and Event Bus have no
  dependencies on other Phase 1 components and are the three roots.
- Logging Interface and Storage Interface both depend only on core
  services (Service Registry, Event Bus, Configuration Manager) and, in
  Logging's case, optionally on Storage Interface.
- Provider Interface is dependency-free in Phase 1 (its `NullAIProvider`
  implementation performs no real work) and is a sibling of Storage
  Interface, not a dependent of it.
- Memory Manager depends on Storage Interface.
- Context Manager depends on Memory Manager and Event Bus; it does not
  depend on Provider Interface in Phase 1 (see Context Manager's
  Dependencies section) — that dependency is added in Phase 2.
- This diagram matches the Phase 1 subset of
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#dependency-graph)'s
  overall Dependency Graph; nothing here depends on any component from
  Phase 2 onward, satisfying the Roadmap's "no component in this phase
  depends on anything outside it."

---

# Initialization Order

Derived directly from the Dependency Diagram, a valid topological
initialization order is:

1. Configuration Manager
2. Service Registry
3. Event Bus
4. Logging Interface
5. Storage Interface
6. Provider Interface (`NullAIProvider` registration)
7. Memory Manager
8. Context Manager

This is the order the Kernel's Module Discovery step must produce given
each module's declared dependencies; it is deterministic for a fixed set
of Phase 1 modules and does not depend on filesystem enumeration order or
any other non-deterministic input.

---

# State Management

- Every Phase 1 module (all nine components except the Configuration
  Manager, which is loaded before Module Discovery and is not itself
  driven through this state machine) follows the `Module` lifecycle state
  machine defined in
  [010_Core_Kernel](010_Core_Kernel.md#module-lifecycle):
  `Discovered → Initialized → Started → Stopped → Unloaded`, with
  `Failed` reachable from `Initialized` (on `init()` error) and from
  `Started` (on unrecoverable runtime error).
- State transitions are owned exclusively by the Module Lifecycle Manager
  inside the Core Kernel; no component transitions its own state directly
  or another component's state.
- Configuration is immutable after boot in Phase 1 (see Configuration
  Manager's Events Produced); there is no "configuration state" beyond
  loaded/not-loaded.
- The only cross-module state shared outside the Service Registry's
  singleton instances is what flows through the Event Bus (events) and
  through the Memory Manager (persisted memory items) — no component
  holds a reference to another component's internal state directly.
- Working Memory state is keyed by `sessionId` and is the only Phase 1
  state that is explicitly bounded and short-lived by design, per
  [050_Memory_Model](050_Memory_Model.md#working-memory); all other
  component state (registry bindings, subscriptions, storage handles) is
  process-lifetime.

---

# Thread Safety

Phase 1 targets a single-process, asynchronous (non-blocking I/O,
cooperative concurrency) execution model, consistent with the Event Bus
being described as in-process transport only, per
[010_Core_Kernel](010_Core_Kernel.md#event-bus). Within that model:

- The Event Bus must support concurrent `emit()` calls from multiple
  modules without interleaving corrupting delivery order per event type;
  per-type publish order is preserved (see Event Bus Dependencies /
  `040_Event_Model.md`'s Routing section), but there is no guarantee of
  relative order *across* different event types.
- Event handlers must be safe to invoke concurrently with themselves, per
  [040_Event_Model](040_Event_Model.md#async-execution) — a Phase 1
  subscriber handler (e.g. on `ContextStageCompleted` or
  `MemoryItemWritten`) must not assume it is the only in-flight
  invocation of itself.
- The Storage Interface's `LocalStorageProvider` must serialize concurrent
  writes to the same key so that two concurrent `write()` calls for the
  same key do not interleave partial writes; concurrent writes to
  different keys may proceed independently.
- The Service Registry's `register()`/`resolve()` calls occur only during
  the single-threaded boot sequence in Phase 1 (Core Service Init and
  Module Init/Start are sequential per Initialization Order above); Phase
  1 does not require the Service Registry itself to be safe for
  concurrent registration after boot, since no Phase 1 component
  registers anything post-boot.
- The Memory Manager's `writeWorking`/`writeLongTerm` calls for the same
  `sessionId` or `itemId` must not race; the Memory Manager serializes
  writes to the same logical item using the same guarantee the Storage
  Interface provides at the key level, rather than introducing a separate
  locking mechanism (KISS — reuse the one guarantee already required
  below it).

---

# Failure Recovery

Failure recovery in Phase 1 operates at two levels, both already specified
by referenced documents and made concrete here:

**Module-level (boot-time and runtime):**
- Per [010_Core_Kernel](010_Core_Kernel.md#error-boundaries), a module
  fault is contained to that module; it transitions to `Failed`, emits
  `ModuleFailed`, and does not crash the Kernel process or any other
  module.
- A `Failed` module in Phase 1 is not automatically restarted (supervised
  restart is Future Work per Core Kernel); it remains `Failed` until an
  operator or test harness explicitly reinitializes it.
- A `Failed` module during the initial boot sequence halts boot entirely
  (see Core Kernel Error Handling) — Phase 1 draws a hard line between
  "a module fails after the system is already `Ready`" (contained, system
  keeps running) and "a module fails while other modules are still
  starting" (boot halts, since a partially-booted system is treated as an
  undefined state the Constitution does not permit shipping).

**Event-level:**
- Per [040_Event_Model](040_Event_Model.md#retry) and
  [040_Event_Model](040_Event_Model.md#dead-letter-handling), a failed
  event handler is retried per its type's retry policy (or the Event
  Bus's `eventBus.defaultRetryPolicy` default) with exponential backoff,
  and moved to dead-letter state once retries are exhausted, persisted via
  the Storage Interface (see Event Bus Error Handling's Phase 1
  Resolution).
- Dead-lettered events in Phase 1 are inspectable via a direct
  `StorageProvider.query()` against the dead-letter key namespace; a
  dedicated administrative capability to browse/replay them is Phase 3+
  (it depends on the Capability Model), so Phase 1 exposes this only at
  the storage level, not through a user-facing tool.

No Phase 1 component implements automatic cross-module failure
compensation (e.g. rolling back a Memory Manager write because a
downstream Context Manager stage later failed) — per the Constitution's
KISS principle, this is not required until a real transactional need
appears, and none exists within Phase 1's stub-heavy scope.

---

# Testing Strategy

Per the Constitution's coding standard ("No feature merges without tests
covering its interface contract at minimum"), Phase 1 testing is organized
per component and per cross-cutting behavior:

**Per-component unit tests** (one suite per component above), each
covering:
- Every public interface method's documented success path.
- Every documented error path (e.g. `UnregisteredServiceError`,
  `InvalidEventError`, `MemoryRetrievalError`, `StorageIOError`,
  `ConfigurationError`, `ProviderNotImplementedError`).
- Lifecycle transitions specific to that component (e.g. Storage
  Interface `init()` failing to `Failed` when its path is unwritable).

**Cross-component integration tests**, required by the Roadmap's Phase 1
Definition of Done:
- **Boot test**: Kernel boots with Service Registry, Event Bus, and
  Configuration Manager operational, in the Initialization Order above,
  and reaches `Ready`.
- **Event round-trip test**: a sample event type is registered, emitted by
  a test producer, and received by a test subscriber through the Event
  Bus, exercising schema validation and routing.
- **Storage-backed retrieval test**: the Memory Manager's `query()`
  returns results sourced from the `LocalStorageProvider` implementation
  of the Storage Interface (not a mock), satisfying "Memory Model's
  Retrieval API returns results against the storage-backed
  implementation."
- **Context Manager stub wiring test**: a full `processInput →
  retrieveContext → assemblePrompt → postProcessOutput` call sequence
  emits one `ContextStageCompleted` event per stage on the Event Bus, in
  order.
- **Shutdown test**: the Shutdown Sequence completes within
  `kernel.shutdownTimeoutMs` per module, in reverse Initialization Order,
  with no module receiving a call after it has stopped.
- **Isolation test**: a module forced to fail during `start()` (test
  double) causes boot to halt and does not leave any already-started
  module unstopped, per Core Kernel Error Handling.

**Out of scope for Phase 1 testing:** any test that requires a real AI
provider response, a real Knowledge Graph traversal, or a real plugin —
those depend on components not built until Phase 2/3, per Scope above; a
Phase 1 test suite that requires them is scoped incorrectly and should be
moved to the corresponding later phase's test plan.

---

# Definition of Done

Phase 1 is complete when all of the following hold, which is a
refinement — not a replacement — of
[900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-1---foundation)'s
Definition of Done:

1. The Kernel boots through Configuration → Core Service Init → Module
   Discovery → Module Init/Start → Ready without manual intervention, and
   the Boot test (Testing Strategy) passes in CI.
2. Service Registry, Event Bus, and Configuration Manager are operational
   and resolvable by every other Phase 1 module, per the Initialization
   Order.
3. The Event schema is versioned and documented (this document's Event
   payloads, plus any additional Phase 1 event types registered during
   implementation), and the Event round-trip test passes.
4. The Storage Interface has exactly one working `LocalStorageProvider`
   implementation, and the Storage-backed retrieval test passes against
   it (not a mock).
5. The Memory Manager's `query()` returns real, ranked results per
   [050_Memory_Model](050_Memory_Model.md#retrieval), sourced from the
   Storage Interface.
6. The Context Manager's four stage methods exist with the interfaces
   defined in this document, stub-implemented as specified, wired to the
   Event Bus, and the Context Manager stub wiring test passes.
7. The Provider Interface (`AIProvider`) is defined exactly as specified,
   with `NullAIProvider` registered and resolvable, and no Phase 1
   component attempts a real invocation through it.
8. The Logging Interface is available to every module at `init()` and
   used by at least the Kernel's own boot/shutdown logging.
9. All Phase 1 components pass their unit tests and the integration tests
   listed in Testing Strategy, in CI.
10. No Phase 1 component's implementation imports or depends on any
    interface or concrete type owned by `020` (beyond the Context Manager
    stub interfaces defined here), `030`, `060`, `080` (beyond the
    Provider Interface frozen here), `090`, `100`, or `110` — satisfying
    "no component in this phase depends on anything outside it."
11. Every **Phase 1 Resolution** called out in this document is either
    (a) still valid and unchanged, or (b) has been reconciled back into
    its source architecture document (`010`, `040`, `050`, `070`, `080`)
    via a documentation update landed in the same change that altered the
    resolved behavior, per the Constitution's Documentation Policy.
