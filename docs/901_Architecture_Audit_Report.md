# 901 Architecture Audit Report

Status: Draft
Scope: `docs/**`, `README.md`, `.github/**` on branch `dev`
Audit date: 2026-07-26

This report is read-only research output. It does not modify any existing document. Findings reference source documents by number/name rather than duplicating their content.

---

# Executive Summary

The PAIOS architecture set (`000`–`110`, `900`) is broadly well-structured, consistently uses "Future Work" sections for aspirational content, and maintains a clean dependency graph across most modules (010, 030, 040, 070, 100, 110 form a DAG). However, the audit found one significant, self-compounding architectural defect — a three-way contradiction and circular control-flow claim among `020_Context_Pipeline.md`, `080_AI_Router.md`, and `090_Prompt_Builder.md` over who assembles and dispatches the prompt — plus systemic duplication of cross-cutting concerns (versioning, retry/backoff, permissions) that violates the Constitution's own DRY principle. Several core interfaces (`EventBus`, `Configuration Service`, `Module`, `MemoryAPI`, `GraphAPI`) are referenced pervasively but never formally specified, and six roadmap-listed components (CLI, Desktop UI, Settings, Logging, Connectors, External APIs) have no architecture document at all — a gap the Roadmap itself already flags. The GitHub issue templates under `.github/ISSUE_TEMPLATE/` are present but empty, which will silently break the Roadmap's planned GitHub Issue mapping.

None of these issues require a redesign of the system's core principles. They require: (1) resolving the 020/080/090 ownership conflict before Phase 2 implementation begins, (2) consolidating the four duplicated cross-cutting policies into single authoritative sections referenced elsewhere, (3) adding formal interface blocks for the small set of un-specified but heavily-depended-on APIs, and (4) filling in the issue templates and the six missing component docs (or explicitly deferring them with owners and target phases).

## Overall Score (/100)

**68 / 100** — Sound foundational principles and phase structure, undermined by one unresolved circular design contradiction in the request/prompt path, pervasive duplication of cross-cutting policy, and a number of missing formal interfaces. No blocking issues prevent Phase 1 work, but Phase 2 (Prompt Builder / AI Router) must not start until the circular contradiction is resolved.

---

## Critical Issues
Priority: Critical

1. **Circular / contradictory ownership of prompt construction and dispatch** across `020_Context_Pipeline.md` (Prompt Assembly, Context Optimization, Token Management), `080_AI_Router.md` ("sole path… only input the router accepts"), and `090_Prompt_Builder.md` (claims to be the mandatory intermediary between the two). Each document treats itself as authoritative and none of the three cross-reference the other two's overlapping claims. `020`'s own sequence diagram shows Assembly handing off directly to the Provider, bypassing Prompt Builder entirely, while `080` claims its only input source is `020`. This is a true cycle in "who calls whom," not simple duplication, and directly blocks Phase 2 implementation as scoped in `900_Implementation_Roadmap.md`.
2. **Token Management and Context Optimization are independently claimed as authoritative, deterministic responsibilities by both `020` and `090`** (budget enforcement against the provider's context window; dedup/compression of low-priority context). Implementing both as written would produce two independent, possibly conflicting trimming/budgeting passes over the same content.
3. **Safety filtering has no owner in the actual control-flow diagram.** `090_Prompt_Builder.md` asserts mandatory pre-injection and post-assembly safety scans, but `020_Context_Pipeline.md`'s own sequence diagram sends the assembled prompt straight to the Provider with no safety stage present at all. If `020`'s diagram is implemented literally, no safety filtering ever runs.

## Major Issues
Priority: High

1. **Four cross-cutting policies are independently and redundantly specified** rather than defined once and referenced: versioning semantics (`000`, `030`, `040`, `070`), retry/backoff policy (`040`, `080`, `110`), context-window budgeting/optimization (`020`, `090` — see Critical), and permission models (`030` capability permissions vs. `100` plugin manifest permissions, never cross-referenced). This is a direct instance of the DRY violation the Constitution itself prohibits ("Duplication of logic across plugins, modules, or documents is a defect to be refactored away").
2. **Kernel `Module` lifecycle and Plugin SDK `Plugin` lifecycle use different state names** (Discovered/Initialized/Started/Stopped/Unloaded/Failed vs. Installed/Validated/Loaded/Initialized/Active/Suspended/Deactivating/Uninstalled/Failed) despite `010_Core_Kernel.md` explicitly claiming "both built-in kernel services and external plugins share the same lifecycle contract." The two state machines are not shown to be the same contract, or one extending the other.
3. **Roadmap Phase 2 Definition of Done requires exercising AI Router failover/retry via integration test, but Phase 2's own scope only requires one Provider Adapter.** Failover is meaningless with a single adapter. The Roadmap's own §Risks section acknowledges this but the fix (a second adapter before Phase 2 sign-off) is not reflected in the Phase 2 DoD itself.
4. **Six roadmap-listed components have no architecture document**: CLI, Desktop UI, Settings, Logging, Connectors, External APIs (self-flagged in `900_Implementation_Roadmap.md` §Risks). Logging in particular is referenced pervasively (e.g., `010`'s Module context injection) despite having no owning document, and Roadmap Phase 4 DoD requires end-to-end traceable logs across Kernel/Event Model/AI Router — undeliverable without a Logging spec.
5. **`.github/ISSUE_TEMPLATE/architecture.md`, `bug_report.md`, and `feature_request.md` are all empty (0 bytes).** The Roadmap's planned GitHub Issue Breakdown depends on functioning templates; empty templates will silently produce blank issues.

## Medium Issues

1. **`README.md` and `.github/CONTRIBUTING.md` describe a `main ← dev ← feature/*` three-tier branch model, while `000_Project_Constitution.md`'s Branching Strategy section only describes `main` plus short-lived `feature/`, `fix/`, `docs/` branches** and states "`main` is always releasable" with no mention of an intermediate `dev` tier. The Constitution should be treated as authoritative per its own precedence rules, but it does not currently describe the branch this audit itself was requested against.
2. **README's repository structure (`docs`, `core`, `sdk`, `plugins`) does not map to the eleven architecture-doc components** (Event Model, Storage, Memory, Knowledge Graph, Context Pipeline, Prompt Builder, AI Router, Workflow Engine, plus the six undocumented components above). No document states which folder each component's code will live in.
3. **Documentation template inconsistency**: `000`–`070` (excluding structure of `080`) use "## Purpose" headings with interfaces embedded in prose/diagrams; `080`, `090`, `100`, `110` use "## Goal / Scope / Design / Interfaces" headings with explicit interface blocks. `070_Storage_Architecture.md` is interface-heavy (`StorageProvider`) but uses the older template and has no "## Interfaces" section, which is inconsistent with its content density.
4. **Cross-reference style is inconsistent**: `000`–`060`/`080` use markdown links with anchors; `090`, `100`, `110` use bare backtick filenames with no links.
5. **Roadmap Phase 1 scopes Context Pipeline and Memory Model but not Knowledge Graph, yet Context Pipeline's Memory Retrieval stage queries the Knowledge Graph directly in its own diagram** — an unstated Phase 1 dependency that the Roadmap's dependency-graph diagram gets right but its phase bullet list omits.
6. **No stated rationale for the docs numbering bands** (gap at 002–009, jump from 110 to 900). The convention is inferable from practice (increment by 10; 900s = process) but never formally documented in the Constitution's Documentation Policy.

## Minor Issues

1. Ambiguity in whether Memory Retrieval fans out to Knowledge Graph and Memory Store as independent sibling sources (per `020`'s diagram) or exclusively through a single unified `MemoryAPI` that internally syncs with the graph (per `050`'s Retrieval section) — likely resolvable by a one-line clarification in either document.
2. `090_Prompt_Builder.md`'s Variable Injection sequence diagram shows a direct synchronous plugin call (`PB->>Plugin: resolve capability defaults`) which appears to conflict with `030_Capability_Model.md`'s "capabilities do not call each other directly" rule, unless Prompt Builder is explicitly exempted as not itself a capability (never stated).
3. No document defines what "authenticated session" or "user identity" concretely means, despite `070_Storage_Architecture.md`'s encryption model depending on "keys derived from user-controlled credentials."

---

## Missing Documents

- CLI (self-flagged, Roadmap Phase 4/5)
- Desktop UI (self-flagged, Roadmap Phase 4/5)
- Settings (self-flagged)
- Logging (self-flagged; also a load-bearing cross-cutting gap, see Major #4)
- Connectors (self-flagged)
- External APIs (self-flagged)
- Security / threat model (unifying document — current security content is fragmented across `030` Permission Model, `070` Encryption, `100` plugin sandboxing, with no document describing the composed trust boundary)
- Testing strategy (Constitution requires interface-contract test coverage; no document defines test types, infrastructure, or coverage bar)
- Deployment / packaging / release process (no document connects `main` branch state to a shipped build/version)
- System-level versioning policy (per-artifact versioning exists four times over; no document ties these together for a coordinated release)
- Auth / identity / multi-user model
- System-wide observability/monitoring (only `110_Workflow_Engine.md` has a Monitoring section, scoped to workflow runs only)
- Multi-device sync conflict resolution at the storage/blob level (distinct from `060`'s entity-level conflict resolution)

## Missing Interfaces

- `EventBus.emit(event)` / `EventBus.subscribe(type, handler)` — used everywhere, never formally specified
- `Configuration Service` interface (e.g. `ConfigService.get(key)`) — referenced by `010`, never defined
- `Module` interface (`init(context)`, `start()`, `stop()`, `unload()`) — used throughout `010`/`030`, no formal interface block (contrast with Plugin SDK's explicit `Plugin` interface)
- `Capability.describe()` return type `CapabilitySchema` — referenced, never defined
- `Capability Registry.register(capability)` and discovery/query methods — shown only in diagrams
- `MemoryAPI.query(context)` — used as the retrieval entry point, no formal contract/signature
- `GraphAPI.traverse(startId, relationshipTypes, depth)` — used in a diagram only, no interface block; Memory Model and Knowledge Graph are the only two component docs with no "## Interfaces" section at all
- `WorkflowEngine` `Step.execute(context) -> StepResult` — `StepResult`'s shape is never defined
- Logging interface — no signature anywhere, despite pervasive references

## Missing Components

- Provider Adapter concrete implementation ownership (Roadmap Phase 2 item; no document assigns which module owns the first concrete adapter)
- Embedding generation path (Roadmap Phase 2 item feeding Knowledge Graph and semantic memory; no document claims ownership of actually calling an embedding model)
- Dead-letter queue storage backend (`040` defers this to Future Work; `070` never claims it either — falls in a gap between the two)
- A formally named "Migration" capability (`070`'s migration sequence diagram uses an unnamed "Admin" actor and an implied capability that `030`/`100` never define)
- Baseline system health/observability plugin or service (illustrative examples exist in `010`/`040` prose, but no document owns building it)

---

## Architecture Risks

1. The 020/080/090 circular contradiction is the largest single risk: if implementation proceeds against any one document literally before the conflict is resolved, three incompatible designs could get built in parallel across overlapping Phase 1/2 work (Roadmap explicitly allows phase overlap).
2. Three independently specified retry/backoff models (Event Model, AI Router, Workflow Engine) with no defined composition rule risk multiplicative retry storms when a workflow step invokes a capability that emits a retried event while the AI Router is itself independently retrying a failover internally.
3. Divergent Kernel `Module` vs. Plugin SDK `Plugin` lifecycle state machines risk incompatible assumptions in code that treats them as one shared contract, per `010`'s claim.
4. Undefined reconciliation between Capability Model permission denial and Workflow Engine recovery: a workflow step failing due to a revoked permission mid-run has no defined recovery semantics.
5. Encryption's dependency on "user-controlled credentials" rests on an undefined authentication/identity foundation.
6. All architecture docs are `Status: Draft` with open TBDs (Roadmap self-flagged Risk #1); this audit's contradictions are pre-existing inter-document drift, which is a stricter defect than the implementation drift the Roadmap's Phase 6 DoD anticipates ("no drift between architecture documents and implemented behavior") — that DoD cannot be met until the document-to-document contradictions found here are resolved first.

## Dependency Problems

- **Circular reference (see Critical #1):** `020 ↔ 080 ↔ 090` — each document treats itself as directly adjacent to the other two in the control flow, with no single consistent direction.
- **Ambiguous parallel dependency:** `050 Memory Model` and `060 Knowledge Graph` are described in `020`'s diagram as independent sibling sources fanned out to by Context Pipeline, but in `050`'s own Retrieval section as a single unified API that syncs with the graph internally — bordering on a cycle depending on which document's diagram is authoritative.
- **Clean DAG confirmed** among `010`, `030`, `040`, `070`, `100`, `110` — no cycles found in this subset.
- Roadmap's Dependency Graph diagram already encodes the *intended* resolution of the 020/080/090 conflict (`020 → 090 → 080`), but the prose of `020` and `080` themselves has not been updated to match — meaning the Roadmap is ahead of the documents it depends on.

---

## Suggested Document Changes

*(Documents are not modified by this report; these are recommendations for a follow-up documentation pass.)*

1. In `020_Context_Pipeline.md`, narrow the Prompt Assembly, Context Optimization, and Token Management sections to state that `090_Prompt_Builder.md` is the authoritative owner of prompt construction, template resolution, context merging, safety filtering, and budget enforcement; update the sequence diagram to route through Prompt Builder before the Provider.
2. In `080_AI_Router.md`, update "sole input" language to name `090_Prompt_Builder.md`'s output (not `020`'s Prompt Assembly stage) as the only accepted input.
3. In `090_Prompt_Builder.md`, add explicit cross-references to the `020` and `080` sections it supersedes, so readers of either document are pointed to the authoritative source.
4. Consolidate the four duplicated versioning-scheme write-ups into one canonical definition (candidate home: `000_Project_Constitution.md`), with `030`/`040`/`070` referencing it instead of restating MAJOR/MINOR/PATCH semantics.
5. Consolidate the three duplicated retry/backoff write-ups similarly, with `040_Event_Model.md` as the likely canonical home given it's the lowest-level mechanism, and `080`/`110` referencing it while noting their domain-specific extensions only.
6. Add a one-line cross-reference between `030_Capability_Model.md`'s Permission Model and `100_Plugin_SDK.md`'s manifest permissions clarifying whether they are the same list or two distinct approval flows.
7. Reconcile `010_Core_Kernel.md`'s Module lifecycle and `100_Plugin_SDK.md`'s Plugin lifecycle state diagrams, or explicitly state they are two separate lifecycle contracts (removing the "shared contract" claim).
8. Add formal "## Interfaces" sections to `050_Memory_Model.md` and `060_Knowledge_Graph.md` defining `MemoryAPI` and `GraphAPI` signatures, matching the style already used in `080`/`090`/`100`/`110`.
9. Reconcile `000_Project_Constitution.md`'s Branching Strategy with the `main ← dev ← feature/*` model actually described in `README.md` and `.github/CONTRIBUTING.md` — pick one and update the other two.
10. Add a short note to the Constitution's Documentation Policy explaining the numbering-band convention (000s, 0N0s incrementing by 10, 900s) to make the existing informal practice explicit.
11. Standardize on one document template (Goal/Scope/Design/Interfaces, as used by `080`/`090`/`100`/`110`) across `000`–`070` in a future editorial pass, and standardize cross-reference style (markdown links with anchors).

## Suggested Repository Changes

1. Populate `.github/ISSUE_TEMPLATE/architecture.md`, `bug_report.md`, and `feature_request.md` — currently empty, which will produce blank GitHub issues under the Roadmap's planned issue-breakdown workflow.
2. Add a mapping (in `README.md` or a new short document) from each numbered architecture doc's component to its eventual source folder, since the current `docs`/`core`/`sdk`/`plugins` structure does not obviously accommodate eleven-plus distinct components.
3. Confirm and document whether `dev` is a permanent branch tier (matching README/CONTRIBUTING) or should be treated as a short-lived integration branch under the Constitution's model, and update whichever document is stale.

## Suggested GitHub Issue Breakdown

1. **[Critical] Resolve 020/080/090 prompt-construction ownership conflict** — assign one document as authoritative owner of prompt assembly, context optimization, token budgeting, and safety filtering; update sequence diagrams in all three documents to match.
2. **[Critical] Reconcile Context Pipeline and AI Router control-flow diagrams** with Prompt Builder inserted, per the Roadmap's own dependency graph.
3. **[High] Consolidate duplicated versioning policy** into one canonical section with cross-references from `030`, `040`, `070`.
4. **[High] Consolidate duplicated retry/backoff policy** into one canonical section with cross-references from `080`, `110`.
5. **[High] Reconcile Capability Model and Plugin SDK permission models** with an explicit cross-reference or unified manifest schema.
6. **[High] Reconcile Kernel Module and Plugin SDK Plugin lifecycle state machines.**
7. **[High] Author Logging architecture document** — required for Roadmap Phase 4 DoD (end-to-end traceable logs).
8. **[High] Fix Roadmap Phase 2 DoD/Risk inconsistency** — require a second Provider Adapter explicitly in the Phase 2 Definition of Done, not only in Risks.
9. **[Medium] Populate empty GitHub issue templates.**
10. **[Medium] Add formal Interfaces sections to Memory Model and Knowledge Graph.**
11. **[Medium] Reconcile branching-strategy description** across Constitution, README, and CONTRIBUTING.
12. **[Medium] Add repository-folder-to-component mapping document or README section.**
13. **[Low] Author Security/Threat Model, Testing Strategy, Deployment, and Auth/Identity documents** (can be scoped as one epic with four sub-issues, targeted before Phase 4/5 per Roadmap's own acknowledged need).
14. **[Low] Standardize document template and cross-reference style** across all `0NN` documents.
15. **[Low] Document the numbering-band convention** in the Constitution.

## Recommended Implementation Order

1. Resolve the 020/080/090 circular contradiction (Critical #1–3) — this blocks any correct Phase 2 implementation and should be treated as a Phase 1 exit criterion, ahead of writing Context Pipeline stub code that Prompt Builder would later have to unwind.
2. Consolidate the four duplicated cross-cutting policies (versioning, retry, permissions) so Phase 1–3 code has one policy to implement against, not several near-identical ones.
3. Add the missing formal interfaces (`EventBus`, `Configuration Service`, `Module`, `MemoryAPI`, `GraphAPI`) before or during Phase 1, since Phase 1 explicitly requires "interfaces with stub implementations."
4. Fix the Phase 2 DoD/Risk inconsistency (require a second Provider Adapter) before Phase 2 sign-off.
5. Reconcile Module/Plugin lifecycle state machines before Phase 3, which is the first phase to exercise both together.
6. Author the Logging document before Phase 4, since Phase 4 DoD depends on it directly.
7. Populate the GitHub issue templates immediately — zero-cost fix, unblocks the Roadmap's issue-breakdown process at any time.
8. Defer Security/Threat Model, Testing Strategy, Deployment, and Auth/Identity documents to before Phase 4/5, consistent with the Roadmap's own acknowledged timing, but assign explicit owners now rather than leaving them unowned.
9. Treat documentation template/style standardization and numbering-convention documentation as a low-priority editorial pass, not blocking any implementation phase.
