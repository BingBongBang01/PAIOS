# 930_Phase1_Development_Workflow

Status: Draft

Version: 0.1

Owner: PAIOS

---

## Purpose

This document is the mandatory implementation workflow for every Phase 1
work package defined in
[920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md). It governs how
a work package moves from "not started" to merged, for both human and AI
(Claude Code) contributors. It does not introduce new architecture,
interfaces, or component behavior — those are owned by
[910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
and the architecture documents (`010`–`110`) — and it does not override
[000_Project_Constitution](000_Project_Constitution.md), which remains the
highest-priority document. Every rule below is a Phase-1-scoped
operationalization of the Constitution's Coding Standards, Branching
Strategy, Documentation Policy, and AI Agent Rules, plus
[900_Implementation_Roadmap](900_Implementation_Roadmap.md)'s phase-exit
discipline.

Every future pull request touching Phase 1 code or documentation must
follow this document. A pull request that does not comply is not ready for
review, regardless of what it implements.

---

# Development Lifecycle

Every Phase 1 work package (WP) moves through the same fixed lifecycle,
one WP per pull request, per
[920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md#numbering-and-conventions):

1. **Select** — pick the next WP whose dependencies (per
   [920](920_Phase1_Work_Breakdown.md#dependency-graph)) have already
   merged. Do not start a WP out of dependency order; if two WPs are
   listed under
   [920](920_Phase1_Work_Breakdown.md#parallel-work-opportunities) as
   parallelizable, either may be selected.
2. **Verify readiness** — confirm the WP meets the Definition of Ready
   below before writing any code.
3. **Branch** — create a branch per Branch Naming below.
4. **Implement interface-first** — define the WP's public interfaces
   (types, method signatures, error types, event types) exactly as named
   in its [920](920_Phase1_Work_Breakdown.md) entry and in
   [910](910_Phase1_Core_Foundation_Specification.md), before writing the
   implementation body, per Interface Implementation Rules below.
5. **Implement** — write the implementation and its tests together, not
   as separate passes; a WP is not "code done, tests pending."
6. **Self-verify** — run the Self Verification Checklist below before
   opening a pull request.
7. **Open pull request** — following Pull Request Rules below, scoped to
   exactly one WP.
8. **Review** — at least one review against the Code Review Checklist
   below.
9. **Merge** — only once Merge Requirements below are satisfied.
10. **Confirm Definition of Done** — the WP's own Acceptance Criteria (per
    [920](920_Phase1_Work_Breakdown.md)) and this document's Definition of
    Done below are both satisfied before the WP is considered closed.

No step is skipped, reordered, or combined across two WPs. A pull request
containing more than one WP's changes must be split before review.

---

# Branch Naming

Per [000_Project_Constitution](000_Project_Constitution.md#branching-strategy),
branches are named descriptively and are short-lived. For Phase 1 work
packages specifically:

- Format: `feature/wp-<NN>-<short-description>`, where `<NN>` is the
  zero-padded WP number from
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) (e.g.
  `feature/wp-09-storage-interface`).
- Documentation-only changes (correcting a Phase 1 Resolution, fixing a
  cross-reference) use `docs/<short-description>` per the Constitution's
  existing convention, not the `feature/wp-NN` format, since they are not
  tied to a single work package.
- Bug fixes discovered against already-merged Phase 1 code use
  `fix/<short-description>`, per the Constitution; if the fix is scoped to
  a specific WP's component, prefix the description with the WP number
  (e.g. `fix/wp-09-storage-race-condition`).
- One branch maps to exactly one pull request and exactly one WP (or, for
  `docs/`/`fix/` branches, exactly one self-contained change). Do not reuse
  a branch across multiple WPs, and do not stack an unrelated WP's changes
  onto an open WP branch.
- Branches are rebased or merged against the branch's base frequently
  enough to avoid drift, per the Constitution; a WP branch that has
  fallen more than a few commits behind its base before review should be
  updated before requesting review, not left to be resolved at merge time.

---

# Commit Rules

- Commit messages are descriptive and explain intent, not mechanics, per
  [000_Project_Constitution](000_Project_Constitution.md#branching-strategy).
- Each commit within a WP's branch should represent one coherent step
  (e.g. "Define ConfigurationManager interface and error types", "Implement
  precedence-ordered config merge", "Add ConfigurationManager unit tests")
  rather than a single monolithic commit or an undifferentiated sequence
  of "wip" commits.
- The final commit (or the PR title, if commits are squashed on merge)
  must reference the WP ID, e.g. `WP-09: Implement Storage Interface`.
- Do not amend or force-push over commits already reviewed by another
  person without flagging it in the PR thread — per the Constitution,
  force-pushes to shared branches require explicit coordination; a WP
  branch under active review by someone else counts as shared for this
  purpose.
- No commit introduces commented-out code, stray debug output, or a TODO
  without a tracked issue reference, per
  [000_Project_Constitution](000_Project_Constitution.md#coding-standards).

---

# Pull Request Rules

- **One WP per pull request.** A PR that spans two WP IDs must be split
  before review, per Development Lifecycle above.
- The PR description states the WP ID and title, links to the WP's entry
  in [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md), and lists
  which of that WP's Acceptance Criteria are satisfied.
- The PR description explicitly states whether it depends on another
  open (not-yet-merged) PR; if so, it is marked as blocked and is not
  merged before its dependency, per
  [920](920_Phase1_Work_Breakdown.md#dependency-graph).
- The PR diff touches only the files listed (or reasonably implied) by
  the WP's "Files Expected" entry in
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md); unrelated
  files are not touched, per the Constitution's "keep changes scoped"
  rule.
- The PR includes the WP's required tests in the same PR as the
  implementation — never as a promised follow-up.
- At least one reviewer approval is required before merge, per
  [000_Project_Constitution](000_Project_Constitution.md#branching-strategy).
  No direct pushes to `main`; Phase 1 work lands on `main` (or the
  project's designated integration branch, if one is in active use)
  exclusively via reviewed pull request.
- A PR that fails CI is not merged, and is not force-merged with `--no-verify`
  or an equivalent override, per the Constitution's prohibition on
  skipping hooks/checks without explicit user confirmation.

---

# Repository Structure Rules

- The source-tree layout convention established by WP-01 (per
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md#wp-01--repository-scaffolding))
  is fixed for all of Phase 1: one top-level module per component area
  (`kernel/`, `events/`, `memory/`, `storage/`, `providers/`, `config/`,
  `logging/`, `context/`, plus a `registry/` module for the Service
  Registry). No Phase 1 WP introduces a new top-level module outside this
  set without first amending WP-01's convention in its own reviewed PR.
- Each component's public interface, its implementation(s), and its error
  types live together in that component's module, not scattered across
  unrelated modules — this mirrors
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)'s
  per-component structure (Purpose, Responsibilities, Public Interfaces,
  etc., all colocated per component).
- Tests live alongside (or in a clearly mirrored test-tree location for)
  the component they test; a Phase 1 component's tests are never located
  inside another component's module.
- Cross-component integration tests (per
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md#wp-20--phase-1-integration-test-suite-and-definition-of-done-verification))
  live in a dedicated integration-test location, not inside any single
  component's module, since they exercise more than one component by
  design.
- No component's module imports directly from another component's
  internal (non-exported) implementation files; cross-component
  dependencies go through the Service Registry and each component's
  published interface, per the Constitution's Interface-First and
  Dependency Inversion principles.

---

# File Naming Rules

- File and module names describe the responsibility they hold, matching
  the component/interface names used in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  and [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) (e.g. a
  file defining the `StorageProvider` interface is named for
  `StorageProvider`/`storage-provider`, not a generic name like `types` or
  `utils`).
- Interface definitions and their concrete implementations are
  distinguishable by name (e.g. `storage-provider.ts` for the interface,
  `local-storage-provider.ts` for `LocalStorageProvider`), consistent with
  [910](910_Phase1_Core_Foundation_Specification.md)'s naming of interface
  vs. implementation types throughout every component section.
- Error types for a component are named and grouped consistently with
  their component (e.g. `StorageIOError` lives with the Storage Interface
  module, not in a shared catch-all errors file spanning multiple
  components) — this keeps DRY at the type-definition level and avoids a
  single file becoming an undocumented cross-component dependency.
- Event type definitions (e.g. `KernelReady`, `MemoryItemWritten`,
  `ContextStageCompleted`) are named identically to the event `type` field
  documented in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md),
  so the name in code and the name on the wire never diverge.
- Test files are named after the unit or integration behavior they verify
  (e.g. a test file for WP-09's encryption-at-rest acceptance criterion is
  discoverable by a name referencing storage encryption, not a generic
  `test1`/`misc` name).

---

# Interface Implementation Rules

- Every Phase 1 public interface is written and reviewed **before** its
  implementation body, per the Constitution's Interface-First principle
  and per Development Lifecycle step 4 above. A PR that adds an
  implementation without the interface already present in the same PR
  (interface-first within a WP, not across separate PRs) does not comply.
- No Phase 1 component's interface (as named in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md))
  is altered by a work package other than the one that owns it in
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md), except where
  a later WP explicitly extends a prior WP's interface (e.g. WP-13 and
  WP-14 each extend `MemoryManager`, as named in their own entries). Any
  other interface change requires updating
  [910](910_Phase1_Core_Foundation_Specification.md) in the same PR, per
  Documentation Update Rules below.
- Consumers depend on the interface type only, resolved via the Service
  Registry; no Phase 1 code constructs a concrete implementation directly
  or imports a concrete class where an interface/token is available, per
  [000_Project_Constitution](000_Project_Constitution.md#coding-standards).
- No provider-specific or storage-backend-specific type crosses an
  adapter boundary (`StorageProvider`, `AIProvider`); adapters translate
  to and from PAIOS-native types only, per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#storage-interface)
  and
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#provider-interface).
- Every interface method's documented inputs, outputs, and error types (as
  specified in `910`) are implemented exactly as named — a WP does not
  add an undocumented parameter, an undocumented return field, or an
  undocumented thrown error type without first updating `910` in the same
  PR.
- Interface Segregation applies at Phase 1 granularity: a component does
  not gain a method on its public interface that is not required by a
  concrete, already-scheduled consumer named in `910` or `920` — no
  speculative interface surface, per the Constitution's KISS principle.

---

# Testing Requirements

- Every WP's own "Tests Required" entry in
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) is the
  minimum, non-negotiable test set for that WP's PR; a PR is not complete
  without it, per the Constitution's "no feature merges without tests
  covering its interface contract at minimum."
- Unit tests cover every documented success path and every documented
  error path (every named error type) for the interfaces a WP introduces
  or extends, per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#testing-strategy).
- Integration tests that span more than one component (per
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md)'s WP-05,
  WP-06, WP-07, WP-16, WP-18, WP-19, and WP-20 entries) are added by the
  WP that first makes the cross-component behavior real, not deferred to
  a later "testing phase" — Phase 1 has no separate testing phase; quality
  is built in per WP, and WP-20 only consolidates and re-verifies, it does
  not backfill missing tests from earlier WPs.
- Tests for a WP run against real Phase 1 dependencies wherever
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) specifies "not
  a mock" (e.g. WP-14's and WP-20's storage-backed retrieval tests); a
  mock is used only where the WP's own entry does not require a real
  dependency (e.g. synthetic test modules/tokens in WP-03 and WP-06).
- A WP's tests must fail if run against the pre-WP state of the codebase
  (i.e., they actually exercise the new behavior) and pass against the
  post-WP state; a test that would pass unchanged before and after the WP
  is not a valid test for that WP.
- No test depends on a component from a WP later in
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md#recommended-pull-request-order)
  than the one under test, per that document's ordering rule that no task
  depends on unfinished future work.
- CI runs the full test suite (all previously merged WPs' tests plus the
  current PR's new tests) on every PR; a PR is not merged if it causes a
  regression in any previously passing test.

---

# Documentation Update Rules

Per [000_Project_Constitution](000_Project_Constitution.md#ai-agent-rules)
rule 7 ("update documentation in the same change whenever behavior,
interfaces, or architecture shift"):

- If a WP's implementation requires deviating from
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  (a signature must change, a Phase 1 Resolution turns out to be
  unworkable), the PR updates `910` in the same change — it does not ship
  a silent divergence between the document and the code.
- If a WP's scope, files, or acceptance criteria must change from what
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) specifies, the
  PR updates `920` in the same change and notes the deviation and its
  reason in the PR description.
- Every **Phase 1 Resolution** flagged in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  that a WP's implementation touches is re-examined at implementation
  time: if it is confirmed correct, no action is needed; if implementation
  reveals it should be reconciled back into its source architecture
  document (`010`, `040`, `050`, `070`, `080`), that reconciliation is
  either done in the same PR or filed as a tracked follow-up issue
  referenced in the PR description — it is never silently left
  inconsistent.
- A WP that introduces a new configuration key, event type, or error type
  not already named in `910` documents it in `910` in the same PR before
  merge; code and documentation are updated together, never
  documentation-as-a-followup, per the Constitution's Documentation
  Policy.
- README or CONTRIBUTING updates are made in the same PR if a WP changes
  how the repository is built, tested, or run (e.g. WP-01 establishing the
  build/test tooling).
- Documentation changes describe the current, actual state introduced by
  the PR; anything not yet true is marked "Future Work," never presented
  as already implemented, per the Constitution's Documentation Policy.

---

# Code Review Checklist

A reviewer confirms each of the following before approving a Phase 1 PR:

1. The PR corresponds to exactly one WP ID from
   [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md), and its
   description links to that WP.
2. Every listed Acceptance Criterion for the WP is met, with a
   corresponding test.
3. Every interface, event, error type, and configuration key introduced
   matches
   [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
   exactly, or `910` was updated in the same PR to match a deliberate,
   explained deviation.
4. No file outside the WP's "Files Expected" scope was modified without
   justification in the PR description.
5. No concrete implementation is depended upon directly by another
   component; all cross-component access goes through an interface
   resolved via the Service Registry.
6. No provider- or storage-backend-specific type crosses an adapter
   boundary.
7. Error handling matches Error Handling Standards below — no missing
   documented error type, no added defensive handling for conditions that
   cannot occur internally.
8. Logging calls (if any) match Logging Standards below.
9. Tests exercise real dependencies where required (not silently
   downgraded to mocks) and fail against pre-PR code.
10. No dependency on a component from a later work package or a later
    Phase (`020` beyond stubs, `030`, `060`, `080` beyond the Provider
    Interface, `090`, `100`, `110`).
11. Commit messages and branch name follow Commit Rules and Branch Naming
    above.
12. Any required documentation update (per Documentation Update Rules) is
    present in the same PR.
13. CI is green.

A PR missing any of the above is sent back for changes, not approved with
follow-up comments promising a later fix — except where item 4's
"justification" or a documented, tracked follow-up issue (per
Documentation Update Rules) explicitly allows deferral.

---

# Self Verification Checklist

Before opening a pull request, the contributor (human or Claude Code)
confirms, in order:

1. Re-read the WP's full entry in
   [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) and the
   corresponding component section in
   [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
   — do not rely on memory of either document.
2. Confirm every dependency listed in the WP's "Dependencies" field has
   already merged; if not, stop and do not open the PR.
3. Confirm the interface was written and is stable before the
   implementation body was written (Interface Implementation Rules).
4. Run the full local test suite (not only the new WP's tests) and
   confirm no regression.
5. Run linting/formatting/build tooling established by WP-01 and confirm
   it passes clean.
6. Diff the changed files against the WP's "Files Expected" list; remove
   or justify anything outside it.
7. Re-read every Acceptance Criterion in the WP's entry and manually
   confirm each one is demonstrably satisfied by a specific test.
8. Confirm no new interface, event, error type, or configuration key is
   undocumented in `910`.
9. Confirm the PR description states the WP ID, links the WP entry, lists
   satisfied Acceptance Criteria, and states any open-PR blocking
   dependency.
10. Confirm the branch name matches Branch Naming above.

Only after all ten checks pass does the contributor open the pull
request.

---

# Merge Requirements

A Phase 1 PR is merged only when all of the following hold simultaneously:

1. At least one reviewer approval is recorded, per
   [000_Project_Constitution](000_Project_Constitution.md#branching-strategy).
2. Every item in the Code Review Checklist above is confirmed by that
   review.
3. CI passes in full — build, lint, and the entire test suite (existing
   plus new) — with no skipped or disabled checks.
4. The PR's branch is up to date with its base (rebased or merged
   recently enough that no unresolved conflict exists), per Branch Naming
   above.
5. Every WP the PR depends on (per its own "Dependencies" field) is
   already merged.
6. No outstanding, unresolved reviewer comment remains open without
   either a follow-up commit addressing it or an explicit reviewer
   acknowledgment that it is deferred (and, if deferred, tracked as a
   follow-up issue per Documentation Update Rules).
7. The merge does not use `--no-verify`, a force-push over review history
   without coordination, or any other bypass of the checks above, per the
   Constitution's AI Agent Rules.

---

# Definition of Ready

A work package is ready to start implementation only when:

1. Its entry exists in
   [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) with all
   required fields populated (ID, Title, Objective, Scope, Files
   Expected, Dependencies, Public Interfaces, Acceptance Criteria, Tests
   Required, Estimated Complexity, Blocking Issues, Follow-up Tasks).
2. Every WP listed in its "Dependencies" field has already merged to the
   integration branch, per Merge Requirements above.
3. Any "Blocking Issues" noted in its
   [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) entry are
   either resolved or explicitly acceptable to proceed against (e.g.
   WP-08's file-sink limitation is a documented, intentional partial
   scope, not a blocker to starting WP-08 itself).
4. The corresponding section(s) of
   [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
   are read and understood by the implementer before branching — the
   Development Lifecycle's "Verify readiness" step is not satisfied by
   skimming.
5. No open, unmerged PR already claims the same WP ID.

A WP that fails any of these checks is not started; the contributor
either resolves the gap first or selects a different, ready WP.

---

# Definition of Done

A work package is done only when:

1. Its pull request has merged per Merge Requirements above.
2. Every Acceptance Criterion in its
   [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) entry is
   verified passing in CI on the merged state (not only pre-merge on the
   branch).
3. Every test in its "Tests Required" field exists, runs in CI, and
   passes.
4. Any documentation updates required by Documentation Update Rules are
   merged in the same PR.
5. Its "Follow-up Tasks" (per
   [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md)) are either
   captured as the next WP in sequence (if they map to an existing WP) or
   filed as a tracked issue (if they do not).
6. No regression was introduced in any previously-done WP's tests.

Phase 1 as a whole is done only when every WP in
[920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md) is done by this
definition and
[920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md#definition-of-phase-1-completion)'s
own completion criteria are all satisfied.

---

# Coding Standards

Phase 1 code follows
[000_Project_Constitution](000_Project_Constitution.md#coding-standards)
in full; the points below are Phase-1-specific emphases, not replacements:

- Every public module exposes its interface before any concrete
  implementation is written (see Interface Implementation Rules).
- No global mutable state; all Phase 1 state lives behind the Service
  Registry, the Storage Interface, or the Memory Manager's documented
  interfaces, per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#state-management).
- Functions and classes have one clearly named responsibility; prefer
  several small units over one large one — a Phase 1 component's
  implementation file is organized by responsibility (e.g. the Memory
  Manager's write path, retrieval path, and forgetting path are distinct
  units even though they share one public interface across WP-12 through
  WP-15).
- Comments explain *why*, never *what*; no commented-out code; no TODO
  without a tracked issue.
- SOLID applies at Phase 1 granularity exactly as in the Constitution;
  in particular, Interface Segregation means a Phase 1 interface is not
  widened beyond what `910` and the owning WP's Acceptance Criteria
  require.
- KISS applies directly to every "Phase 1 Resolution" in `910`: implement
  the resolution as written, do not build a more general mechanism than
  the resolution calls for on the theory that Phase 2 might need it —
  Phase 2 additions are handled by Phase 2 WPs, not preempted now.
- DRY applies across WPs: a WP does not reimplement logic already
  provided by an earlier WP's interface (e.g. WP-13 does not reimplement
  its own storage retry/serialization logic — it uses the Storage
  Interface's existing guarantees, per
  [910](910_Phase1_Core_Foundation_Specification.md#thread-safety)).

---

# Error Handling Standards

- Errors are handled at system boundaries only — I/O, external input,
  and cross-component interface calls — per
  [000_Project_Constitution](000_Project_Constitution.md#coding-standards)
  and
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)'s
  Error Handling sections. No Phase 1 component adds a guard for a
  condition that cannot occur internally (e.g. a Service Registry
  resolution of a token that component's own code always registers
  itself).
- Every named error type in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  (e.g. `UnregisteredServiceError`, `InvalidEventError`,
  `MemoryRetrievalError`, `MemoryWriteError`, `StorageIOError`,
  `ConfigurationError`, `UnknownConfigKeyError`,
  `ProviderNotImplementedError`, `InvalidInputError`,
  `KernelBootError`) is thrown exactly where `910` specifies it, and
  nowhere else undocumented.
- A caught fault that a component cannot itself resolve propagates to its
  Error Boundary (per
  [910](910_Phase1_Core_Foundation_Specification.md#core-kernel)'s Error
  Handling and
  [910](910_Phase1_Core_Foundation_Specification.md#failure-recovery)) —
  it is never silently swallowed or logged-and-ignored in place of
  propagating.
- A module that fails during boot halts the Kernel's boot sequence, per
  [910](910_Phase1_Core_Foundation_Specification.md#error-handling); no
  Phase 1 code introduces a "continue booting in degraded mode" path,
  since Phase 1 has no defined degraded-mode contract.
- Retries (Event Bus handler retries, per
  [910](910_Phase1_Core_Foundation_Specification.md#event-bus)) use the
  documented backoff policy; no Phase 1 component adds its own ad hoc
  retry loop around a dependency that already has a documented retry
  policy (this would violate DRY and the single-producer-of-truth rule
  for retry behavior).
- A read/query returning "no result" (e.g. `StorageProvider.read()` on a
  missing key, `MemoryManager.hardDelete()` on a missing id) is a
  documented non-error outcome and must not be represented as a thrown
  error or converted into one by a consumer.

---

# Logging Standards

- Every Phase 1 component logs through the Logging Interface
  (`Logger`/`LoggerFactory`, per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#logging-interface)),
  never through a direct console/stdout call or a component-local logging
  mechanism.
- A component obtains its `Logger` via
  `LoggerFactory.forModule(moduleId)` at `init()` and reuses that instance
  for its lifetime; it does not construct a new `Logger` per call site.
- Log level usage: `debug` for internal implementation detail useful only
  during development; `info` for lifecycle milestones (module started/
  stopped, boot phase completed); `warn` for a recovered or degraded
  condition (a retried handler, a decayed memory item); `error` for a
  fault that reached an Error Boundary or a boundary-level rejection
  (`StorageIOError`, `MemoryWriteError`, etc.).
- Log entries that relate to a specific request or event include the
  `correlationId` field, per
  [910](910_Phase1_Core_Foundation_Specification.md#logging-interface),
  so a chain of related log lines can be traced even though full
  cross-component traceability is a Phase 4 deliverable.
- A logging call never throws and never blocks the calling component's
  own logic; a sink failure degrades to the console sink internally, per
  [910](910_Phase1_Core_Foundation_Specification.md#error-handling-8).
- No log entry includes a raw, unencrypted long-term memory item's full
  content or a raw configuration secret (e.g. the value behind
  `storage.local.encryptionKeySource`); log entries reference identifiers
  (`itemId`, `sessionId`, `moduleId`) rather than the sensitive payload
  itself, consistent with the Constitution's Human-First data ownership
  stance carried by
  [050_Memory_Model](050_Memory_Model.md#long-term-memory).

---

# Dependency Rules

- A Phase 1 component depends only on: other Phase 1 components' public
  interfaces (per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#dependency-diagram)),
  the Service Registry, the Event Bus, and the Logging Interface. It does
  not depend on any interface or concrete type owned by `020` (beyond the
  Context Manager's own frozen stub interfaces), `030`, `060`, `080`
  (beyond the Provider Interface frozen in `910`), `090`, `100`, or `110`,
  per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#definition-of-done)
  and
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md#definition-of-phase-1-completion).
- No circular dependency is introduced among Phase 1 components; the
  dependency direction for every component matches
  [910](910_Phase1_Core_Foundation_Specification.md#dependency-diagram)
  and [920](920_Phase1_Work_Breakdown.md#dependency-graph) exactly. A PR
  that requires a component to depend "back" on something that depends on
  it is rejected and referred back to `910`/`920` for resolution before
  any code is written.
- No kernel service (Configuration Manager, Service Registry, Event Bus,
  Logging Interface) depends on a non-core-service Phase 1 component
  (Memory Manager, Context Manager, Storage Interface, Provider
  Interface), per
  [010_Core_Kernel](010_Core_Kernel.md#kernel-services)'s rule that "no
  kernel service depends on a plugin" applied at Phase 1's finer
  granularity.
- External (third-party library) dependencies are added only where a
  Phase 1 component's scope genuinely requires them (e.g. an embedded
  storage library for WP-09); no external dependency is added
  speculatively for a capability Phase 1 does not use, per the
  Constitution's KISS and Non-Goals sections.
- A dependency between two Phase 1 components is always expressed through
  the Service Registry (interface resolution), never as a direct
  import of another component's concrete class or a direct constructor
  call across module boundaries, per Interface Implementation Rules
  above.

---

# Backward Compatibility Rules

- Within Phase 1, an already-merged WP's public interface is additive-only
  once a later WP has started depending on it (e.g. WP-14 and WP-15 may
  each add new methods to `MemoryManager`, per
  [920_Phase1_Work_Breakdown](920_Phase1_Work_Breakdown.md), but must not
  remove or change the signature of methods WP-12/WP-13 already
  delivered and that other merged code already calls).
- If a WP genuinely requires a breaking change to an already-merged
  interface (a signature must change, not just extend), the PR making that
  change explicitly updates every existing caller in the same PR and
  updates
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  to reflect the new signature — an interface is never left in a state
  where the code and `910` disagree.
- Event schemas follow
  [040_Event_Model](040_Event_Model.md#event-versioning)'s semantic
  versioning discipline from the first version onward: a Phase 1 event
  type's payload is not changed in a backward-incompatible way without a
  MAJOR version bump and an explicit migration note, even though Phase 1
  has, by construction, no external subscriber outside the Phase 1
  codebase yet.
- Configuration keys introduced in one WP are not renamed or removed by a
  later WP without updating every reader of that key in the same PR and
  updating `910`'s Configuration section for the affected component.
- Nothing in Phase 1 breaks the Roadmap's stated invariant that "no
  component may be implemented ahead of the components it depends on," per
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#dependency-graph)
  — a backward-compatibility fix never involves reaching forward into an
  unbuilt Phase 2+ component to patch a Phase 1 gap.

---

# Future Phase Compatibility

- Every Phase 1 interface frozen in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  is written so that Phase 2 can implement its "Future Extension Points"
  (per each component's section in `910`) without changing the Phase 1
  interface's method signatures — e.g. the Context Manager's four stage
  methods, the `AIProvider` interface, and the `MemoryManager.query()`
  signature are treated as stable contracts for Phase 2 to build against,
  not drafts Phase 2 is expected to redesign.
- No Phase 1 implementation hard-codes an assumption that only
  `NullAIProvider` or only a single `StorageProvider` binding will ever
  exist; Phase 1 code depends on the interface's contract, not on the
  cardinality of Phase 1's own registrations, so Phase 2/5's multi-adapter
  and multi-backend registrations (per
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-2---ai-layer)
  and
  [900_Implementation_Roadmap](900_Implementation_Roadmap.md#phase-5---integration))
  do not require reopening Phase 1 code.
- Every stub left by Phase 1 (the Context Manager's stage bodies, the
  Memory Manager's relationship-index no-op, `NullAIProvider`) is
  documented as a stub in `910` and is replaceable in Phase 2 by
  swapping an implementation behind the Service Registry, not by editing
  the Phase 1 interface — per
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#future-extension-points-1)
  and
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md#future-extension-points-3).
- Event types, configuration keys, and error types introduced in Phase 1
  are namespaced and scoped so that Phase 2–6 additions do not collide
  with them (per
  [040_Event_Model](040_Event_Model.md#event-schema)'s per-module
  namespacing rule); a Phase 1 PR does not choose a generic, unnamespaced
  identifier that a later phase would be forced to work around.
- Any Phase 1 Resolution in
  [910_Phase1_Core_Foundation_Specification](910_Phase1_Core_Foundation_Specification.md)
  that explicitly defers full behavior to a later phase (e.g. the Logging
  Interface's Phase 4 extension, the Storage Interface's key-management
  UX deferred to Phase 4 Settings) is implemented in Phase 1 only to the
  extent `910` specifies — Phase 1 does not partially implement a Phase
  4+ concern in a way that later work must first undo.
