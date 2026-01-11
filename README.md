# ollama-sgpt

A powerful ShellGPT alternative powered by Ollama for local, private AI assistance.

[![Tests](https://github.com/sadorect/ollama-sgpt/actions/workflows/test.yml/badge.svg)](https://github.com/sadorect/ollama-sgpt/actions/workflows/test.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔒 **Privacy-first**: Uses local Ollama models - no API keys, no data leakage
- ⚡ **Fast**: Streaming responses for real-time interaction
- 🎯 **Role-based prompting**: Built-in modes for shell commands, code, and explanations
- 💾 **Conversation history**: Persistent chat history across sessions
- 🛡️ **Error handling**: Graceful failures with helpful troubleshooting
- 🧪 **Well-tested**: 67% test coverage with comprehensive unit tests
- 🔧 **Developer-friendly**: Clean codebase with proper packaging

## Quick Start

### Prerequisites

- Python 3.9 or higher
- [Ollama](https://ollama.ai) installed and running

### Installation

```bash
# Clone the repository
git clone https://github.com/sadorect/ollama-sgpt.git
cd ollama-sgpt

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
cd ollama-sgpt
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Start interactive chat
sgpt

# One-shot query
sgpt "explain quantum computing"

# Shell command mode
sgpt --shell "list all files recursively"

# Code generation mode
sgpt --code "fibonacci function in python"

# Explain mode
sgpt --explain "docker run -it ubuntu bash"

# Use different model
sgpt --model mistral "hello world"

# Disable streaming
sgpt --no-stream "what is AI?"
```

## Configuration

Create `~/.ollama_sgpt.yaml` to customize settings:

```yaml
model: llama3
ollama_url: http://localhost:11434/api/chat
stream: true
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=ollama_sgpt

# Lint code
ruff check ollama_sgpt

# Format code
black ollama_sgpt

# Type check
mypy ollama_sgpt
```

## Project Status

**Version:** 0.2.0 (Alpha)  
**Status:** Week 1 Complete - Foundation & Infrastructure ✅

### Completed (v0.2.0)

- ✅ Complete package configuration
- ✅ Error handling with health checks
- ✅ Testing infrastructure (22 tests)
- ✅ CI/CD pipeline
- ✅ Documentation (LICENSE, CONTRIBUTING, CHANGELOG)

### Coming in Week 2

- 🔄 Multi-session support
- 🔄 Context file loading
- 🔄 Enhanced REPL with multi-line input

### Planned Features

See [PHASE1_IMPLEMENTATION_PLAN.md](PHASE1_IMPLEMENTATION_PLAN.md) for the complete roadmap.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [shell_gpt](https://github.com/TheR1D/shell_gpt)
- Powered by [Ollama](https://ollama.ai)

## Links

- **Documentation**: [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md)
- **Roadmap**: [PHASE1_IMPLEMENTATION_PLAN.md](PHASE1_IMPLEMENTATION_PLAN.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
