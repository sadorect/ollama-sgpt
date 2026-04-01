# ollama-sgpt Deployment Roadmap

## Objective

Ship `v0.3.0` as a dependable cross-platform CLI release on GitHub and PyPI.

See also: [v0.3 Release Tracker](release-tracker.md) for the ordered implementation backlog, dependencies, and ship checklist ownership.

For this project, "conclusive deployment" means:

- Linux, macOS, and Windows users can install and run the tool without repo-specific knowledge.
- `--shell` output is trustworthy for the selected shell.
- `--execute` safety behavior is consistent across Unix and Windows command families.
- Documentation, package metadata, tests, and release artifacts all describe the same product state.

## Current Baseline (2026-03-27)

- Core CLI behavior exists: chat, sessions, context loading, REPL, and command execution.
- Cross-platform shell hardening is underway and should remain the `v0.3.0` focus.
- The remaining risk is not feature absence as much as release inconsistency:
  - docs and defaults are partially out of sync
  - CI/release quality gates are incomplete
  - benchmark and rollout artifacts are not yet committed

## Definition of Done

`v0.3.0` is ready to deploy only when all of the following are true:

- CI passes on `ubuntu-latest`, `windows-latest`, and `macos-latest`.
- Python support is verified on `3.9` through `3.12` where practical.
- `--shell` produces command-only output for `bash`, `powershell`, and `cmd`.
- Windows high-risk and critical command patterns are covered by tests and confirmation flow.
- Install and first-run docs are verified on Linux, macOS, and Windows PowerShell.
- Package metadata, README, docs, and runtime defaults are aligned.
- A benchmark baseline is committed for shell accuracy, safety behavior, and latency.
- Release artifacts are published successfully to:
  - GitHub Releases
  - TestPyPI
  - PyPI
- A rollback path is documented and tested.

## Deployment Strategy

This is a CLI distribution rollout, not a server rollout. Deployment should happen in three channels:

### 1) Staging

- Build wheel and sdist locally in CI.
- Publish prerelease artifacts to TestPyPI.
- Create GitHub prerelease notes for `v0.3.0-rc1`.

### 2) Validation

- Install from TestPyPI on:
  - Ubuntu
  - Windows PowerShell
  - macOS
- Run smoke scenarios with at least one general model and one code-oriented model.
- Confirm docs match actual install and runtime behavior.

### 3) General Availability

- Tag `v0.3.0`.
- Publish to PyPI.
- Publish GitHub Release with release notes, benchmark summary, and upgrade guidance.

## Roadmap At A Glance

```text
Phase 0   Phase 1         Phase 2            Phase 3              Phase 4
Align  -> Hardening   -> Release Candidate -> Staged Validation -> General Release
2-3 d     Week 1         Week 2              Week 3               Week 4
```

## Phase Plan

### Phase 0: Alignment and Cleanup (2-3 days)

**Goal:** Remove ambiguity before hardening work continues.

**Tasks**
- Align version, release status, and defaults across:
  - `pyproject.toml`
  - `README.md`
  - installation/configuration docs
- Resolve config-path drift and document one canonical config format.
- Remove stale claims about test counts, coverage, and release status.
- Define the exact shell support promise for `bash`, `powershell`, and `cmd`.

**Exit Criteria**
- A contributor can answer "what ships in v0.3.0?" from the docs alone.
- No documentation contradicts runtime defaults.

---

### Phase 1: Hardening (Week 1)

**Goal:** Make the product behavior trustworthy across supported platforms.

**Tasks**
- Finish shell-specific prompting and command-only output handling.
- Complete command extraction coverage for:
  - fenced shell blocks
  - multiline commands
  - plain-text command responses
  - PowerShell and cmd examples
- Complete Windows safety parity for `--execute`.
- Add or tighten preflight checks for missing external tools where it prevents confusing failures.
- Ensure first-run connection/model diagnostics are actionable.

**Exit Criteria**
- All release-blocking shell and executor tests pass locally and in CI.
- Manual smoke checks succeed on Windows PowerShell and Linux.

---

### Phase 2: Release Candidate (Week 2)

**Goal:** Freeze behavior and establish measurable quality gates.

**Tasks**
- Expand CI matrix to the final supported platform/Python set.
- Add machine-readable test artifacts on failure:
  - JUnit or equivalent test reports
  - coverage artifact
- Fix release pipeline gaps such as missing `coverage.xml` generation if upload depends on it.
- Create benchmark suite for:
  - shell command accuracy
  - safety false positives / false negatives
  - latency by model
- Commit the first benchmark baseline.
- Cut `v0.3.0-rc1` on GitHub and publish to TestPyPI.

**Exit Criteria**
- CI is green on all required runners.
- Benchmark baseline exists and is referenced in release notes draft.
- RC artifacts install successfully from TestPyPI.

---

### Phase 3: Staged Validation (Week 3)

**Goal:** Prove the release works outside the dev environment.

**Tasks**
- Run clean-machine install tests from TestPyPI on:
  - Ubuntu
  - macOS
  - Windows PowerShell
- Execute smoke scenarios:
  - basic prompt
  - `--shell`
  - `--shell --dry-run`
  - session creation
  - context loading
- Validate docs by following them exactly as written.
- Collect RC issues and classify them:
  - release blocker
  - post-release patch
  - backlog
- Fix blockers and, if needed, ship `v0.3.0-rc2`.

**Exit Criteria**
- No open release blockers remain.
- Install docs have been proven verbatim on all supported platforms.

---

### Phase 4: General Release (Week 4)

**Goal:** Publish `v0.3.0` and stabilize immediately after release.

**Tasks**
- Bump version and finalize changelog.
- Publish wheel and sdist to PyPI.
- Publish GitHub Release with:
  - benchmark summary
  - supported platforms/shells
  - known limitations
  - upgrade notes
- Monitor issues for 48 hours after release.
- Triage any post-release regressions into:
  - docs fix
  - hotfix `v0.3.1`
  - defer to `v0.4`

**Exit Criteria**
- PyPI release is live and installable.
- GitHub release notes are public.
- No critical regression is reported in the first 48 hours.

## Implementation Plan by Workstream

### Workstream A: Product Correctness

**Scope**
- Shell prompt fidelity
- Response normalization
- Command extraction
- First-run diagnostics

**Implementation**
1. Make shell behavior explicit in prompts and runtime handling.
2. Normalize shell outputs before display and before execution.
3. Add regression tests for shell-specific response formats.
4. Verify interactive and one-shot flows behave the same way.

**Deliverables**
- Stable shell-mode behavior
- Test coverage for `bash`, `powershell`, and `cmd`

---

### Workstream B: Safety and Execution

**Scope**
- Risk classification
- Confirmation flow
- Windows command-family parity
- Missing-tool preflight

**Implementation**
1. Finalize Windows high-risk and critical pattern coverage.
2. Confirm auto-confirm is blocked for dangerous classes.
3. Expand test cases for PowerShell and cmd destructive commands.
4. Add documentation examples for allowed, warned, and blocked behaviors.

**Deliverables**
- Cross-platform execution safety parity
- Clear end-user warnings and examples

---

### Workstream C: Packaging and Install UX

**Scope**
- PyPI/TestPyPI publishing
- install docs
- defaults/config consistency

**Implementation**
1. Align package version and development-status metadata.
2. Make `pipx` the first-class install path.
3. Verify fallback `pip` and editable installs.
4. Standardize config path, default model, and example snippets across docs.

**Deliverables**
- Predictable installation story
- Docs that match the shipped package

---

### Workstream D: Quality Gates and Benchmarks

**Scope**
- CI matrix
- coverage/report artifacts
- shell benchmarks

**Implementation**
1. Finish required CI runners and Python versions.
2. Emit artifacts needed for debugging release failures.
3. Add benchmark harness and store the baseline in-repo.
4. Gate release candidates on "no benchmark regression beyond agreed threshold."

**Deliverables**
- Reliable release signal
- Regression visibility over time

---

### Workstream E: Release Engineering

**Scope**
- prerelease process
- changelog
- release notes
- rollback

**Implementation**
1. Define release-candidate tag and publish flow.
2. Draft release notes before final tag.
3. Publish to TestPyPI first, then PyPI after validation.
4. Document rollback and hotfix steps before GA.

**Deliverables**
- Repeatable release process
- Low-risk final deployment path

## Release Checklist

### Must Be Green Before `v0.3.0`

- [ ] CI matrix green on Linux, macOS, and Windows
- [ ] Release-blocking tests pass
- [ ] Shell-mode regression tests pass for `bash`, `powershell`, and `cmd`
- [ ] Executor safety tests cover Windows destructive patterns
- [ ] Benchmark baseline committed
- [ ] Docs verified on clean installs
- [ ] Changelog updated
- [ ] Version bumped consistently
- [ ] TestPyPI install verified
- [ ] PyPI publish dry run verified

### Nice To Have But Not Release Blocking

- [ ] Shell integration helpers
- [ ] Config profiles
- [ ] Command audit trail export
- [ ] Plugin groundwork

## Go / No-Go Review

Hold a final 30-minute release review before tagging `v0.3.0`.

**Inputs**
- CI status
- smoke-test results
- benchmark summary
- docs verification notes
- unresolved issue list

**Go if**
- no critical or high-severity blockers remain
- install path works from TestPyPI on all supported platforms
- docs match runtime behavior

**No-Go if**
- shell output is still inconsistent by platform
- install docs fail on a clean machine
- benchmark or safety regressions are unexplained

## Rollback Plan

If `v0.3.0` ships with a critical regression:

1. Stop promotion and update release notes with a warning.
2. Yank the PyPI release if the defect affects install or basic runtime safety.
3. Publish a GitHub issue labeled `release-blocker`.
4. Cut `v0.3.1` or `v0.3.1-rc1` with the smallest safe fix.
5. Update docs to reflect the temporary limitation until the hotfix is live.

## Post-Deployment Follow-Through

Once `v0.3.0` is stable, the next roadmap can move to `v0.4`:

- session and REPL UX parity, including transcript inspection/export
- shell integration helpers
- shell command describe and command-only piping ergonomics
- custom local roles and prompt profiles
- local request cache with safe defaults
- constrained allowlisted local tool calling
- profile switching
- command audit trail export
- plugin system groundwork
- provider abstraction improvements

See also: [v0.3 Release Tracker](release-tracker.md#post-v03-gap-closure-plan) for the sequenced post-`v0.3` plan.
