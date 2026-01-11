# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Complete package configuration with proper dependencies
- Comprehensive error handling with custom exceptions
- Health check and validation for Ollama connection
- Multi-session support for isolated chat histories
- Context file loading to include file contents in prompts
- Enhanced REPL with multi-line input support
- Safe code execution with confirmation prompts
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- Type hints and documentation

### Changed

- Improved CLI argument parsing with click
- Better error messages and user feedback
- Enhanced streaming output with rich formatting

### Fixed

- Connection timeout issues
- History persistence bugs
- Stream parsing errors

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
