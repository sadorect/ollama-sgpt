# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0-rc1] - 2026-03-31

### Changed

- Prevented live streamed assistant replies from being printed twice after the stream completed
- Aligned README and docs with the current runtime defaults and release story
- Documented supported shell behavior for `bash`, `powershell`, and `cmd`
- Replaced stale configuration, installation, session, usage, and troubleshooting guidance with runtime-accurate docs
- Hardened Windows execution-risk detection for reordered `cmd`/PowerShell deletion patterns and added safer handling for read-only `netsh ... show` queries
- Tightened first-run Ollama diagnostics and missing-command preflight guidance so setup failures point to concrete recovery commands
- Added typo suggestions for missing external tools so near-miss commands like `nmpa` can point users toward `nmap`
- Finalized CI failure artifacts so matrix runs now keep JUnit test reports, coverage XML, and HTML coverage output for debugging
- Added a committed `v0.3` shell benchmark harness and baseline covering extraction accuracy, safety classification, and live local-model latency
- Expanded session UX with transcript inspection/export, true REPL session preload, and an in-memory `temp` scratch session
- Added shell UX helpers including `--describe-shell`, pipe-friendly `--stdout-only`, and opt-in shell integration snippets for Bash, Zsh, and PowerShell
- Added saved custom prompt roles with local storage, CLI management commands, and runtime reuse via `--role`
- Added an opt-in local response cache with inspect/clear commands and cache hits that can be served without a live Ollama call
- Added an opt-in constrained local tool mode with an allowlisted read-only tool set gated by `tools_enabled`
- Closed remaining user-doc gaps around role deletion, transcript inspection/export, scratch sessions, and REPL session preload
- Added `--init` onboarding and `--doctor` diagnostics for local setup, config creation, and Ollama readiness checks

## [0.2.0] - 2026-02-17

### Week 4 Completed - 2026-02-17

#### Added

- Comprehensive documentation system
  - Installation, usage, configuration, troubleshooting guides
  - Sessions, context loading, code execution documentation
  - Safety and security documentation
  - Example configurations and workflows
- Enhanced CLI
  - `--version` flag to display version information
  - Improved `--help` output with detailed descriptions
  - Better error messages and user guidance
- Complete README overhaul
  - "Why ollama-sgpt?" section highlighting privacy focus
  - Feature comparison table with ShellGPT
  - Architecture diagram
  - Comprehensive usage examples
  - Development guide with commands
  - Project statistics (107 tests, >85% coverage, ~2,550 LOC)

### Week 3 Completed - 2026-02-17

#### Added

- Code execution framework with comprehensive safety checks
  - `CodeExecutor` class with 4-tier risk assessment (low/medium/high/critical)
  - Dangerous pattern detection for 30+ risky command patterns
  - Command preview with syntax highlighting
  - Tiered confirmation prompts based on risk level
  - Timeout protection (configurable, default 120s)
  - Output capture and formatted display
  - Command extraction from AI responses (code blocks, inline code, plain text)
- CLI flags for code execution
  - `--execute` / `-e` - Execute AI-generated commands
  - `--yes` / `-y` - Auto-confirm low/medium risk commands (blocked for high/critical)
  - `--dry-run` - Preview commands without execution
- Integrated execution in both modes
  - One-shot command execution
  - Interactive REPL with live execution
  - Execution results stored in session history
- 32 new tests for executor (107 tests total)
  - Risk analysis: 5 tests
  - Command extraction: 7 tests
  - Execution flow: 6 tests
  - Confirmation logic: 6 tests
  - Edge cases: 5 tests
  - Preview functionality: 2 tests

### Week 2 Completed - 2026-02-17

#### Added

- Multi-session support for isolated chat histories
  - Create, list, delete, and manage named sessions
  - Session persistence across runs
  - CLI flags: `--session`, `--list-sessions`, `--delete-session`
- Context file loading to include file contents in prompts
  - Load multiple files with `--context` flag (repeatable)
  - Automatic validation and error handling
  - File summary display
- Enhanced REPL with multi-line input support
  - Prompt-toolkit integration for better UX
  - Multi-line input with Esc+Enter submission
  - Special commands: `/help`, `/clear`, `/history`, `/exit`
  - Command history with arrow keys
  - Better visual formatting
- 55 new tests for Week 2 features (75 tests total)
  - SessionManager: 23 tests
  - Context loading: 17 tests
  - REPL functionality: 15 tests

### Week 1 Completed - 2026-01-11

#### Added

- Complete package configuration with proper dependencies
- Comprehensive error handling with custom exceptions
- Health check and validation for Ollama connection
- Comprehensive test suite with pytest (22 tests)
- CI/CD pipeline with GitHub Actions
- Type hints and documentation

### Planned

- Command history logging and audit trail
- Plugin system for extensibility
- Configuration profiles
- Shell integration helpers
- Performance optimizations

### Changed

- Improved CLI argument parsing and validation
- Better error messages and user feedback
- Enhanced streaming output with rich formatting
- Updated documentation structure

### Fixed

- Version inconsistency between __init__.py and pyproject.toml

## [0.1.0] - 2026-01-11

### Added

- Initial release
- Basic chat functionality
- Streaming support
- Role-based prompting (default, shell, code, explain)
- History persistence
- Interactive mode
- One-shot command mode
- Stdin support

[Unreleased]: https://github.com/sadorect/ollama-sgpt/compare/v0.3.0-rc1...HEAD
[0.3.0-rc1]: https://github.com/sadorect/ollama-sgpt/compare/v0.2.0...v0.3.0-rc1
[0.2.0]: https://github.com/sadorect/ollama-sgpt/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sadorect/ollama-sgpt/releases/tag/v0.1.0
