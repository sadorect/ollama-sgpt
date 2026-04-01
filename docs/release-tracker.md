# v0.3 Release Tracker

## Purpose

This document turns the deployment roadmap into an execution backlog for `v0.3.0`.

Use it to answer:

- what gets built next
- which work items are on the critical path
- what must be true before release candidate and general availability

## Working Agreement

- Only merge work that moves `v0.3.0` toward release readiness.
- Treat docs/metadata drift as a release blocker when it affects installation, defaults, or safety expectations.
- Prefer small PRs with one main purpose each.
- Do not start RC or release work until all blocking correctness items are green.

## Board Columns

Use this board shape for GitHub Projects or issue labels:

| Column | Meaning |
| --- | --- |
| Backlog | Defined but not ready to start |
| Ready | Unblocked and ready for pickup |
| In Progress | Active implementation |
| Validation | Code merged, awaiting docs/QA/install verification |
| Blocked | Waiting on dependency or decision |
| Done | Fully shipped for `v0.3.0` |

## Milestones

| Milestone | Target | Purpose |
| --- | --- | --- |
| M0 | Week 0 | Align docs, metadata, and support promise |
| M1 | Week 1 | Finish product hardening and platform correctness |
| M2 | Week 2 | Cut release candidate with quality gates |
| M3 | Week 3 | Validate RC on clean installs |
| M4 | Week 4 | Publish GA release and monitor |

## Critical Path

The shortest path to deployment is:

1. Align metadata and runtime defaults.
2. Finalize shell correctness behavior.
3. Finalize Windows safety parity and tests.
4. Fix CI artifacts and release pipeline gaps.
5. Add benchmark baseline.
6. Publish and validate `v0.3.0-rc1`.
7. Publish `v0.3.0`.

If any step above slips, release slips.

## Ordered Backlog

### R0-01: Align Version, Defaults, and Release Messaging

**Why**

The repo currently mixes release states and default values across package metadata and docs.

**Scope**

- Align version references
- Align development status wording
- Align default model, config path, and install guidance

**Likely Files**

- `pyproject.toml`
- `README.md`
- `docs/installation.md`
- `docs/configuration.md`
- `CHANGELOG.md`

**Dependencies**

- None

**Definition of Done**

- One canonical config path is documented.
- One canonical default model is documented.
- README, changelog, and package metadata describe the same release state.

---

### R0-02: Define and Document Supported Shell Matrix

**Why**

The release promise depends on explicit shell support, not best-effort behavior.

**Scope**

- Define supported shells and limitations
- Document exact promise for `bash`, `powershell`, and `cmd`
- Call out unsupported or partially supported edge cases

**Likely Files**

- `README.md`
- `docs/usage.md`
- `docs/execution.md`
- `docs/roadmap.md`

**Dependencies**

- R0-01

**Definition of Done**

- A user can see which shells are supported and what "command-only output" means.

---

### R1-01: Harden Shell Prompt Selection and Output Normalization

**Why**

This is the core product behavior for `--shell`.

**Scope**

- Ensure shell-specific prompting is used everywhere shell mode is invoked
- Normalize streamed and non-streamed shell responses consistently
- Fail clearly when no executable command can be extracted

**Likely Files**

- `ollama_sgpt/cli.py`
- `ollama_sgpt/roles.py`
- `ollama_sgpt/executor.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_executor.py`

**Dependencies**

- R0-02

**Definition of Done**

- Shell mode returns one command or a clear extraction failure.
- Interactive and one-shot shell behavior match.

---

### R1-02: Complete Windows Safety Parity for `--execute`

**Why**

The current release goal is trustable cross-platform execution safety.

**Scope**

- Finalize PowerShell/cmd high-risk and critical patterns
- Verify confirmation flow for dangerous Windows commands
- Add safe exceptions where needed to avoid noisy false positives

**Likely Files**

- `ollama_sgpt/executor.py`
- `docs/execution.md`
- `tests/unit/test_executor.py`

**Dependencies**

- R1-01

**Definition of Done**

- Representative destructive Windows commands are classified correctly.
- HIGH and CRITICAL commands require manual confirmation.

---

### R1-03: Tighten First-Run Diagnostics and Preflight Checks

**Why**

Users should not need repo knowledge to recover from missing Ollama, missing models, or missing external tools.

**Scope**

- Improve connection and model guidance
- Improve missing-command preflight messaging
- Ensure docs match runtime remediation steps

**Likely Files**

- `ollama_sgpt/cli.py`
- `ollama_sgpt/ollama_client.py`
- `ollama_sgpt/executor.py`
- `docs/troubleshooting.md`
- `docs/installation.md`

**Dependencies**

- R1-01

**Definition of Done**

- Common first-run failures have actionable messages and matching docs.

---

### R1-04: Expand Release-Blocking Regression Tests

**Why**

The release should be gated by behavior, not confidence.

**Scope**

- Add shell extraction matrix tests
- Add Windows safety tests
- Add diagnostics/preflight tests where behavior is user-visible

**Likely Files**

- `tests/unit/test_cli.py`
- `tests/unit/test_executor.py`
- `tests/unit/test_config.py`
- `tests/unit/test_repl.py`

**Dependencies**

- R1-02
- R1-03

**Definition of Done**

- The release-blocking behaviors have explicit tests.

---

### R2-01: Finalize CI Matrix and Failure Artifacts

**Why**

Cross-platform release claims need repeatable CI proof.

**Scope**

- Finalize Linux, Windows, and macOS jobs
- Add test report and coverage artifacts
- Fix any artifact path mismatches

**Likely Files**

- `.github/workflows/test.yml`
- `pyproject.toml`

**Dependencies**

- R1-04

**Definition of Done**

- Every PR runs the required platform matrix.
- Failed runs leave enough artifacts to debug without rerunning locally.

---

### R2-02: Add Benchmark Harness and Baseline

**Why**

The release needs a measurable quality baseline for shell behavior.

**Scope**

- Define benchmark inputs
- Capture command accuracy
- Capture safety false positives and false negatives
- Capture latency by model class

**Likely Files**

- `benchmarks/` or `scripts/benchmarks/`
- `README.md`
- `CHANGELOG.md`
- release notes draft

**Dependencies**

- R1-01
- R1-02

**Definition of Done**

- Benchmark baseline is committed and summarized for release notes.

---

### R2-03: Build and Publish `v0.3.0-rc1` to TestPyPI

**Why**

A release candidate is the first real deployment checkpoint.

**Scope**

- Build wheel and sdist
- Publish prerelease artifacts
- Draft GitHub prerelease notes

**Likely Files**

- release workflow files
- `CHANGELOG.md`
- `README.md`

**Dependencies**

- R2-01
- R2-02

**Definition of Done**

- `v0.3.0-rc1` is installable from TestPyPI.

---

### R3-01: Validate Clean Installs on Linux, macOS, and Windows

**Why**

The product is only deployable if the published artifact works outside the dev machine.

**Scope**

- Install from TestPyPI
- Follow docs exactly as written
- Run smoke scenarios for core flows

**Smoke Scenarios**

- basic prompt
- `--shell`
- `--shell --dry-run`
- `--session`
- `--context`

**Dependencies**

- R2-03

**Definition of Done**

- All supported platforms pass the documented install flow.

---

### R3-02: Resolve RC Blockers and Cut `v0.3.0-rc2` If Needed

**Why**

Validation should lead to explicit blocker resolution, not vague polish.

**Scope**

- Triage all RC findings
- Fix release blockers
- Re-run only the required validation set

**Dependencies**

- R3-01

**Definition of Done**

- No unresolved release blockers remain.

---

### R4-01: Publish `v0.3.0` and Monitor for 48 Hours

**Why**

GA should be deliberate and observable.

**Scope**

- Final version bump
- PyPI publish
- GitHub Release publish
- post-release monitoring and triage

**Dependencies**

- R3-02 or successful R3-01 with no blockers

**Definition of Done**

- `v0.3.0` is live on PyPI and GitHub Releases.
- No critical regression appears in the first 48 hours.

## Suggested Labels

| Label | Use |
| --- | --- |
| `v0.3` | Belongs to the release |
| `release-blocker` | Must be fixed before GA |
| `rc-blocker` | Must be fixed before next RC |
| `platform:windows` | Windows-specific work |
| `platform:macos` | macOS-specific work |
| `platform:linux` | Linux-specific work |
| `area:cli` | CLI/runtime behavior |
| `area:executor` | Execution and safety |
| `area:docs` | Documentation |
| `area:ci` | CI and release workflows |
| `area:packaging` | Packaging and publishing |
| `area:benchmarks` | Benchmark work |

## PR Sequence

Recommended merge order:

1. `docs: align version, defaults, and supported shell messaging`
2. `shell: harden command-only output normalization`
3. `executor: complete windows safety parity`
4. `tests: expand shell and executor release-blocking coverage`
5. `ci: finalize platform matrix and failure artifacts`
6. `benchmark: add v0.3 shell baseline harness`
7. `release: publish rc1 to TestPyPI`
8. `docs: verify and correct clean-install workflows`
9. `release: publish v0.3.0`

## Release Gate Review Template

Use this summary before tagging GA:

| Check | Status | Notes |
| --- | --- | --- |
| Metadata and docs aligned | `DONE` | Runtime defaults, shell support, and install guidance were aligned in R0. |
| Shell regression tests green | `DONE` | Release-blocking CLI, executor, REPL, and benchmark tests are passing locally. |
| Windows safety parity verified | `DONE` | Windows-specific destructive-command coverage and confirmation behavior were hardened in R1. |
| CI matrix green | `TODO` | |
| Coverage/test artifacts valid | `DONE` | Workflow now emits JUnit, `coverage.xml`, and HTML coverage artifacts. |
| Benchmark baseline committed | `DONE` | `benchmarks/baselines/v0.3-shell-baseline.json` committed with `100%` fixture accuracy and `6/6` live accuracy on the selected local models. |
| TestPyPI install verified | `TODO` | |
| Release notes ready | `TODO` | |
| Rollback path confirmed | `TODO` | |

## Not in Scope for `v0.3.0`

Keep these out of the critical path unless they become necessary for release safety:

- plugin system groundwork
- config profiles
- shell integration helpers
- command audit trail export
- provider abstraction redesign

## Post-`v0.3` Gap-Closure Plan

Use this plan after `v0.3.0` ships to close the biggest product gaps with mainstream ShellGPT without giving up `ollama-sgpt`'s core strengths.

### Guardrails To Preserve

These are not negotiable:

- Ollama remains the default and best-supported runtime.
- Generated commands continue to pass through the existing extraction, preflight, risk, and confirmation pipeline.
- New tool or function behavior is opt-in, local-first, and allowlisted.
- Benchmarks and release-blocking tests expand with each new capability.

### Goal

Match the most important day-to-day ShellGPT usability wins while keeping this product:

- local-first
- predictable
- safer by default
- cross-platform for `bash`, `powershell`, and `cmd`

### Phase A: Session and REPL UX Parity

**Why**

The repo already has named sessions and one-shot resume, but interactive resume and session inspection are still rough.

**Scope**

- preload prior session history when entering REPL with `--session`
- add `--show-session NAME` to inspect saved transcripts
- add `--export-session NAME --output FILE` for shareable transcript export
- add optional `temp` session semantics for scratch conversations
- make session lifecycle clearer in help and docs

**Likely Files**

- `ollama_sgpt/cli.py`
- `ollama_sgpt/repl.py`
- `ollama_sgpt/session.py`
- `docs/usage.md`
- `tests/unit/test_cli.py`
- `tests/unit/test_repl.py`
- `tests/unit/test_session.py`

**Definition of Done**

- One-shot and REPL flows resume the same session context.
- Users can inspect and export a session without manually opening JSON files.

---

### Phase B: Shell UX Improvements

**Why**

ShellGPT still feels smoother for command generation and terminal-native usage.

**Scope**

- add a first-class "describe this shell command" workflow
- add an explicit command-only stdout mode for shell piping ergonomics
- add opt-in shell integration helpers for Bash, Zsh, and PowerShell
- keep `cmd` supported for generation even if shell-buffer integration is unavailable there

**Likely Files**

- `ollama_sgpt/cli.py`
- `ollama_sgpt/executor.py`
- `docs/usage.md`
- `docs/execution.md`
- install helper scripts under `scripts/` if needed
- `tests/unit/test_cli.py`

**Definition of Done**

- Users can generate, describe, and pipe commands cleanly.
- Shell integration is opt-in and does not bypass execution safeguards.

---

### Phase C: Custom Roles and Prompt Profiles

**Why**

ShellGPT supports custom roles; `ollama-sgpt` currently exposes only built-in modes.

**Scope**

- support user-defined local roles stored in a predictable config directory
- add list/show/select commands for roles
- allow a role to be combined with sessions and context loading
- keep built-in roles as defaults and examples

**Likely Files**

- `ollama_sgpt/roles.py`
- new role storage helpers under `ollama_sgpt/`
- `docs/configuration.md`
- `docs/usage.md`
- `tests/unit/test_roles.py` or equivalent

**Definition of Done**

- A user can create and reuse local prompt profiles without editing source files.

---

### Phase D: Local Request Cache

**Why**

Caching is a major convenience win, but it must not undermine command freshness or safety.

**Scope**

- add an opt-in local cache keyed by:
  - model
  - role
  - prompt
  - context hash
  - shell type
  - relevant runtime flags
- disable cache by default for `--shell --execute`
- expose clear cache controls and cache inspection commands

**Likely Files**

- new cache module under `ollama_sgpt/`
- `ollama_sgpt/cli.py`
- `docs/configuration.md`
- `docs/usage.md`
- `tests/unit/test_cache.py`

**Definition of Done**

- Repeat requests can return instantly from local cache where safe.
- Cached shell results never bypass the current execution gate.

---

### Phase E: Constrained Tool Calling

**Why**

This is the largest capability gap, but it should be implemented more carefully than mainstream ShellGPT function calling.

**Scope**

- define a small allowlisted tool interface
- start with read-only local tools:
  - file listing
  - file reading
  - git status/log inspection
  - process and system info
- route any shell execution back through the existing `CodeExecutor`
- require explicit config to enable tools
- log tool usage clearly in responses and session history

**Likely Files**

- new tool runtime under `ollama_sgpt/`
- `ollama_sgpt/cli.py`
- `ollama_sgpt/executor.py`
- `docs/execution.md`
- `docs/usage.md`
- new tests for tool routing and safety boundaries

**Definition of Done**

- The model can use a minimal set of local tools without silent side effects.
- No tool path bypasses the existing shell safety checks.

---

### Phase F: Optional Provider Abstraction

**Why**

Broader backend support helps adoption, but should not dilute the Ollama-first story.

**Scope**

- add optional OpenAI-compatible endpoint support
- preserve Ollama as the default install and docs path
- keep provider selection explicit in config and CLI
- benchmark provider-specific shell quality separately

**Likely Files**

- `ollama_sgpt/config.py`
- `ollama_sgpt/cli.py`
- provider client modules under `ollama_sgpt/`
- docs and benchmark files

**Definition of Done**

- Additional providers are optional, documented, and tested.
- Ollama remains the primary and best-verified runtime path.

## Recommended Order

To keep the product coherent, execute the post-`v0.3` plan in this order:

1. Phase A: session and REPL UX parity
2. Phase B: shell UX improvements
3. Phase C: custom roles and prompt profiles
4. Phase D: local request cache
5. Phase E: constrained tool calling
6. Phase F: optional provider abstraction

## Success Criteria

The gap is meaningfully closed when all of the following are true:

- session behavior feels continuous in both one-shot and REPL modes
- shell workflows are easier to generate, inspect, and reuse in-terminal
- users can create local roles without editing project code
- repeat prompts can benefit from local caching where safe
- tool calling exists, but remains transparent and bounded
- none of the above weakens the local-first or safety-first posture

