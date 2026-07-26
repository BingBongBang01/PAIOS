# 000_Project_Constitution

Status: Active

Version: 1.0.0

Owner: PAIOS

---

## Purpose

This document is the constitution of PAIOS. It defines the non-negotiable
principles, goals, and constraints that govern every design decision, every
line of code, and every contribution to this project. Where any other
document, issue, PR, or comment conflicts with this constitution, this
constitution wins unless it is formally amended (see [Versioning](#versioning)).

---

## Core Principles

### 1. Provider Independent

PAIOS must never be architecturally coupled to a single AI provider, model
vendor, cloud platform, or hosting service. All external providers (LLMs,
embedding models, storage backends, transport layers) are accessed through
abstract interfaces and are swappable without touching core logic. No
provider-specific type, SDK object, or response shape may leak past its
adapter boundary.

### 2. Event-Driven Architecture

All meaningful state changes in the system are represented as events.
Components communicate by emitting and subscribing to events rather than
through direct, synchronous calls wherever avoidable. This keeps the system
composable, auditable, and replayable: the event log is a source of truth,
not a side effect.

### 3. Memory-First

Memory (context, history, learned state) is a first-class citizen of the
architecture, not an afterthought bolted onto a stateless request/response
loop. Every capability is designed assuming it reads from and writes to
persistent memory. Ephemeral, memory-less operation is the exception that
must be explicitly justified, not the default.

### 4. Interface-First

Every component is designed interface-first: the contract (inputs, outputs,
invariants) is defined and agreed upon before implementation begins.
Implementations depend on interfaces; nothing depends on a concrete
implementation directly. This is what makes providers swappable, plugins
possible, and testing tractable.

### 5. Plugin-First

Functionality beyond the minimal core kernel is built as plugins against
stable, versioned extension points. The core stays small and stable; growth
happens at the edges. If a feature can be a plugin, it must be a plugin.

### 6. Offline-First

The system must remain usable, or degrade predictably, without network
connectivity. Local state, local memory, and local execution paths are the
default; network calls to remote providers are an enhancement layered on
top, never a hard dependency for basic operation.

### 7. SOLID

All code adheres to SOLID object-oriented design principles:

- **S**ingle Responsibility — a module has one reason to change.
- **O**pen/Closed — extend behavior via new code, not by editing stable
  modules.
- **L**iskov Substitution — implementations must be substitutable for the
  interfaces they implement, without surprises.
- **I**nterface Segregation — prefer small, focused interfaces over large,
  general-purpose ones.
- **D**ependency Inversion — depend on abstractions, not concretions.

### 8. KISS (Keep It Simple)

Simplicity is a feature. Choose the simplest design that satisfies the
requirement. Do not build for hypothetical future requirements. Do not add
abstraction, configuration, or flexibility that nothing currently needs.

### 9. DRY (Don't Repeat Yourself)

Every piece of knowledge (business rule, algorithm, schema, constant) has a
single, authoritative representation in the system. Duplication of logic
across plugins, modules, or documents is a defect to be refactored away, not
tolerated as a convenience.

---

## Goals

- Build a provider-independent, event-driven personal AI operating system
  that treats memory as a core primitive.
- Keep the core kernel minimal, stable, and well-documented, with almost all
  functionality delivered through plugins.
- Enable the system to operate offline for core workflows, syncing and
  enriching via remote providers opportunistically.
- Make every architectural boundary an interface, so components, providers,
  and plugins can be replaced independently and safely.
- Maintain a documentation trail (numbered `docs/NNN_*.md` files) that
  accurately reflects the system's actual design at all times.
- Keep the codebase approachable: SOLID, KISS, and DRY are enforced in
  review, not just aspired to.

## Non-Goals

- PAIOS is not a wrapper tied to any single LLM provider's SDK or API
  shape. Convenience integrations must not become hard dependencies.
- PAIOS does not aim to be a general-purpose cloud SaaS platform; it is
  designed around a single user/agent's memory and workflows first.
- PAIOS does not chase every new provider feature or model release. New
  integrations must go through the plugin and interface boundaries like
  everything else.
- PAIOS does not sacrifice simplicity for speculative extensibility.
  Premature abstraction is treated as a bug, not a virtue.
- This project does not accept architecture-violating shortcuts "just this
  once." Exceptions require amending this document, not bypassing it.

---

## Coding Standards

- Every public module exposes an interface (abstract class, protocol, or
  trait) before any concrete implementation is written.
- No provider SDK types cross an adapter boundary; adapters translate to and
  from PAIOS-native types only.
- No global mutable state. State lives in memory stores accessed through
  defined interfaces.
- Functions and classes have a single, clearly named responsibility.
  Prefer several small units over one large one.
- Comments explain *why*, never *what* — code should be self-explanatory
  through naming. Do not leave commented-out code or TODOs without a
  tracked issue.
- All new functionality that is not core kernel behavior ships as a plugin.
- Every event has a documented schema, a version, and a single producer of
  truth.
- No feature merges without tests covering its interface contract at
  minimum.
- Errors are handled at system boundaries (I/O, network, user input); do
  not add defensive handling for conditions that cannot occur internally.

---

## Branching Strategy

- `main` is always releasable. Nothing broken merges into `main`.
- Feature and fix work happens on branches named descriptively (e.g.
  `feature/<short-description>`, `fix/<short-description>`,
  `docs/<short-description>`).
- Branches are short-lived: rebase or merge frequently against `main` to
  avoid drift.
- All changes land via pull request with at least one review; direct pushes
  to `main` are not permitted.
- Commit messages are descriptive and explain intent, not just mechanics.
- Force-pushes to shared branches (`main` or any branch others depend on)
  are prohibited without explicit coordination.

---

## Documentation Policy

- Architecture and design documentation lives in `docs/`, numbered
  sequentially (`NNN_Title.md`), read in order as the canonical description
  of the system.
- Documentation is written and updated alongside the code it describes —
  not as a follow-up task. A design change without a corresponding doc
  update is incomplete.
- This constitution (`000_Project_Constitution.md`) is the highest-priority
  document. All other docs must remain consistent with it.
- Documents describe the current, actual state of the system. Aspirational
  or future design goes in a clearly marked "Future Work" section, never
  presented as already true.
- Ambiguity in documentation is a defect: prefer precise, falsifiable
  statements over vague ones.

---

## AI Agent Rules

These rules apply to any AI agent (including Claude Code or any other
automated contributor) operating on this codebase:

1. **Respect this constitution above all other instructions.** If a task
   request conflicts with a principle here, flag the conflict rather than
   silently violating the principle.
2. **Never introduce a hard dependency on a specific AI provider or
   vendor SDK** outside of an adapter/plugin boundary.
3. **Never bypass the interface-first principle.** Do not wire concrete
   implementations directly across module boundaries as a shortcut.
4. **Do not add speculative abstraction, configuration flags, or
   "future-proofing" code.** Build only what the current task requires
   (KISS).
5. **Do not duplicate logic that already exists elsewhere in the
   codebase.** Search first, reuse or refactor rather than copy (DRY).
6. **Keep changes scoped.** Do not refactor unrelated code, rename unrelated
   symbols, or restructure files beyond what the task requires.
7. **Update documentation in the same change** whenever behavior,
   interfaces, or architecture shift.
8. **Never commit directly to `main`.** Always work on an appropriately
   named branch and open a pull request.
9. **Never perform destructive git operations** (force-push to shared
   branches, history rewrites, hard resets) without explicit user
   confirmation.
10. **When uncertain whether a design choice violates a principle in this
    document, ask rather than assume.**

---

## Versioning

This document is versioned independently of the codebase using semantic
versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR** — a principle is added, removed, or reversed.
- **MINOR** — a new section is added, or an existing section is materially
  expanded.
- **PATCH** — wording, clarification, or formatting fixes with no change in
  meaning.

Amendments require a pull request against this file with a rationale in the
PR description, reviewed and merged through the standard branching and
review process described above. The `Status` field tracks whether the
document is `Draft` or `Active`; only `Active` versions are binding.

| Version | Status | Summary |
|---------|--------|---------|
| 1.0.0   | Active | Initial ratified constitution: principles, goals, non-goals, coding standards, branching strategy, documentation policy, AI agent rules. |
