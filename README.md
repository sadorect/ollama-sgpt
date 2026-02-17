# ollama-sgpt

A powerful ShellGPT alternative powered by Ollama - privacy-first AI assistance with advanced features.

[![Tests](https://github.com/sadorect/ollama-sgpt/actions/workflows/test.yml/badge.svg)](https://github.com/sadorect/ollama-sgpt/actions/workflows/test.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/sadorect/ollama-sgpt/releases)

## Why ollama-sgpt?

**Privacy-first alternative to ShellGPT** with NO API keys, NO cloud dependency, and NO data leakage. All processing happens locally on your machine using Ollama.

### Key Advantages

- 🔒 **100% Private**: Your data never leaves your machine
- 💰 **Zero Cost**: No API fees, unlimited usage
- ⚡ **Fast**: Local processing, no network latency
- 🎯 **Advanced Features**: Sessions, context loading, safe code execution
- 🧪 **Production-Ready**: 107 tests, >85% coverage, comprehensive safety checks
- 🛡️ **Safe Execution**: 4-tier risk assessment for command execution

## Features

### Core Capabilities

- 🔒 **Privacy-first**: Uses local Ollama models - no API keys required
- ⚡ **Real-time streaming**: Fast, responsive AI interactions
- 🎯 **Role-based prompting**: Specialized modes for shell, code, and explanations
- 💾 **Multi-session management**: Isolated conversation histories
- 📁 **Context loading**: Include file contents in prompts
- 🚀 **Enhanced REPL**: Multi-line input, special commands, command history
- ⚙️ **Safe code execution**: AI-generated commands with security checks
- 🧪 **Well-tested**: 107 comprehensive unit tests
- 🔧 **Developer-friendly**: Clean codebase, type hints, excellent documentation

## Quick Start

### Prerequisites

- Python 3.9 or higher
- [Ollama](https://ollama.ai) installed and running
- A model pulled (e.g., `ollama pull llama3`)

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

### Verify Installation

```bash
# Check version
sgpt --version

# Verify Ollama connection
sgpt "hello"
```

## Usage

### Basic Commands

```bash
# Interactive chat
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

### Advanced Features

#### Multi-Session Management

Organize conversations into isolated sessions:

```bash
# Create/use a session
sgpt --session myproject "how do I use decorators?"

# List all sessions
sgpt --list-sessions

# Continue previous session
sgpt --session myproject "show me an example"

# Delete a session
sgpt --delete-session myproject
```

#### Context Loading

Include file contents in your prompts:

```bash
# Load single file context
sgpt --context main.py "explain this code"

# Load multiple files
sgpt --context app.py --context utils.py --context config.yaml "review this code"

# With session
sgpt --session review --context src/handler.js "suggest improvements"
```

#### Enhanced REPL Mode

Multi-line input with special commands:

```bash
sgpt --session work
>>> def hello():
... |    print("world")    # Press Esc+Enter to submit
... 
AI response...

>>> /help       # Show available commands
>>> /history    # View conversation
>>> /clear      # Clear history
>>> /exit       # Exit REPL
```

#### Safe Code Execution ⚠️

Execute AI-generated commands with safety checks:

```bash
# Execute shell commands (with confirmation)
sgpt --shell --execute "find all large files"

# Preview without executing
sgpt --shell --dry-run "delete old log files"

# Auto-confirm safe commands only
sgpt --shell --execute --yes "create backup directory"

# Interactive execution
sgpt --shell --execute
>>> compress all images in current directory
[AI generates command]
[Risk assessment: MEDIUM]
[Preview with syntax highlighting]
Execute this command? [y/N]: y
[Execution with output]
```

**Safety Features:**
- 4-tier risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- 30+ dangerous pattern detection
- Tiered confirmation prompts
- AUTO-CONFIRM blocked for high-risk commands
- Dry-run mode for safe testing
- Timeout protection

## Configuration

Create `~/.ollama_sgpt.yaml` to customize settings:

```yaml
model: llama3                              # Default model
ollama_url: http://localhost:11434/api/chat  # Ollama API endpoint
stream: true                                # Enable streaming responses
history_file: ~/.ollama_sgpt_history.json  # Chat history location
```

See [docs/configuration.md](docs/configuration.md) for advanced configuration options.

## CLI Reference

### Command Modes

```bash
--shell        # Generate shell commands
--code         # Generate code snippets
--explain      # Explain commands/code
```

### Session Management

```bash
--session NAME, -s NAME     # Use/create session
--list-sessions             # List all sessions
--delete-session NAME       # Delete a session
```

### Context Loading

```bash
--context FILE, -c FILE     # Load file context (repeatable)
```

### Code Execution

```bash
--execute, -e               # Execute generated commands
--yes, -y                   # Auto-confirm (safe commands only)
--dry-run                   # Preview without execution
```

### General Options

```bash
--model MODEL               # Specify model
--no-stream                 # Disable streaming
--version                   # Show version
--help                      # Show help
```

## Examples

See [docs/examples/](docs/examples/) for more comprehensive examples:

- [Session workflows](docs/examples/session_workflows.md)
- [Context loading patterns](docs/examples/context_examples.md)
- [Safe execution scenarios](docs/examples/execution_examples.md)
- [Configuration examples](docs/examples/configs/)

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/sadorect/ollama-sgpt.git
cd ollama-sgpt
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ollama_sgpt --cov-report=html

# Run specific test file
pytest tests/unit/test_executor.py -v

# Run tests matching pattern
pytest -k "test_risk" -v
```

### Code Quality

```bash
# Lint code
ruff check ollama_sgpt

# Format code
black ollama_sgpt

# Type check
mypy ollama_sgpt

# Run all checks
pytest && ruff check ollama_sgpt && mypy ollama_sgpt
```

### Project Statistics

- **Total Tests**: 107 (all passing ✅)
- **Test Coverage**: >85%
- **Lines of Code**: ~2,550 (implementation)
- **Test Code**: ~1,625 lines
- **Modules**: 8 core modules
- **CLI Flags**: 12 options

## Project Status

**Version:** 0.2.0 (Beta)  
**Phase 1 Progress:** 75% Complete ███████████████░░░░░

### ✅ Completed Features (Weeks 1-3)

**Week 1: Foundation & Infrastructure**
- ✅ Complete package configuration
- ✅ Comprehensive error handling with health checks
- ✅ Testing infrastructure (22 tests, CI/CD)
- ✅ Documentation (LICENSE, CONTRIBUTING, CHANGELOG)

**Week 2: Core Features**
- ✅ Multi-session management system
- ✅ Context file loading from multiple files
- ✅ Enhanced REPL with multi-line input (Esc+Enter)
- ✅ Special commands (/help, /clear, /history, /exit)
- ✅ 55 additional tests (75 total)

**Week 3: Code Execution Framework**
- ✅ Safe command execution with 4-tier risk assessment
- ✅ 30+ dangerous pattern detection
- ✅ Command preview with syntax highlighting
- ✅ Tiered confirmation prompts
- ✅ Dry-run and auto-confirm modes
- ✅ 32 additional tests (107 total)

### 🔄 In Progress (Week 4)

- 📝 Comprehensive documentation
- 📚 Example workflows and configurations
- 🎨 Final polish and UX improvements
- 📦 Release preparation (v0.2.0)

### 🚀 Upcoming (Post-v0.2.0)

- Command history logging and audit trail
- Plugin system for extensibility
- Configuration profiles
- Shell integration helpers
- Performance optimizations

See [progressUpdates/](progressUpdates/) for detailed implementation tracking.

## Architecture

```
ollama-sgpt/
├── ollama_sgpt/          # Main package
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration management
│   ├── context.py        # File context loading
│   ├── exceptions.py     # Custom exceptions
│   ├── executor.py       # Code execution framework
│   ├── history.py        # Chat history persistence
│   ├── ollama_client.py  # Ollama API client
│   ├── repl.py           # Enhanced REPL
│   ├── roles.py          # Role-based prompts
│   └── session.py        # Session management
├── tests/                # Test suite (107 tests)
├── docs/                 # Documentation
└── examples/             # Example workflows
```

## Safety & Security

### Command Execution Safety

ollama-sgpt implements multiple safety layers for code execution:

1. **Pattern Detection**: 30+ known dangerous command patterns
2. **Risk Assessment**: LOW → MEDIUM → HIGH → CRITICAL
3. **Tiered Confirmations**:
   - LOW: Press Y (default yes)
   - MEDIUM: Press y (default no)
   - HIGH: Type "yes" explicitly
   - CRITICAL: Type "yes I understand"
4. **Auto-Confirm Limits**: HIGH/CRITICAL always require manual approval
5. **Timeout Protection**: Prevents runaway processes
6. **User Control**: Always cancellable with Ctrl+C

### Privacy Guarantee

- ✅ All processing happens locally
- ✅ No data sent to external APIs
- ✅ No telemetry or usage tracking
- ✅ No API keys or authentication required
- ✅ Your conversations stay on your machine

## Troubleshooting

### Ollama Not Running

```bash
# Start Ollama server
ollama serve

# Check if Ollama is accessible
curl http://localhost:11434/api/version
```

### Model Not Found

```bash
# List available models
ollama list

# Pull a model
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

### Command Execution Issues

If commands won't execute:

1. Ensure you're using `--shell` mode
2. Check if `--execute` flag is present
3. Verify command extraction succeeded
4. Review risk assessment output

For more help, see [docs/troubleshooting.md](docs/troubleshooting.md).

## Comparison with ShellGPT

| Feature | ollama-sgpt | ShellGPT |
|---------|-------------|----------|
| **Privacy** | ✅ 100% local | ❌ Requires OpenAI API |
| **Cost** | ✅ Free, unlimited | ❌ Pay per API call |
| **Sessions** | ✅ Built-in | ❌ Not available |
| **Context Loading** | ✅ Multiple files | ❌ Not available |
| **Multi-line REPL** | ✅ Esc+Enter | ⚠️ Limited |
| **Risk Assessment** | ✅ 4-tier system | ⚠️ Basic |
| **Pattern Detection** | ✅ 30+ patterns | ⚠️ Limited |
| **Dry-run Mode** | ✅ Yes | ❌ No |
| **Test Coverage** | ✅ 107 tests, >85% | ⚠️ Minimal |
| **Documentation** | ✅ Comprehensive | ⚠️ Basic |

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [shell_gpt](https://github.com/TheR1D/shell_gpt)
- Powered by [Ollama](https://ollama.ai)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Enhanced with [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)

## Links

- **Documentation**: [docs/](docs/)
- **Progress Updates**: [progressUpdates/](progressUpdates/)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/sadorect/ollama-sgpt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sadorect/ollama-sgpt/discussions)

---

**Made with ❤️ for the privacy-conscious developer community**
