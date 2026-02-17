# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- Safe code execution with confirmation prompts
- Enhanced CLI with click framework
- More role templates
- Configuration file improvements

### Changed

- Improved CLI argument parsing
- Better error messages and user feedback
- Enhanced streaming output with rich formatting

### Fixed

- Connection timeout issues
- History persistence bugs
- Stream parsing errors
- Version inconsistency between **init**.py and pyproject.toml

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

[Unreleased]: https://github.com/sadorect/ollama-sgpt/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sadorect/ollama-sgpt/releases/tag/v0.1.0
