# Contributing to ollama-sgpt

Thank you for your interest in contributing to ollama-sgpt! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Environment details** (OS, Python version, Ollama version)
- **Error messages** or logs if applicable

### Suggesting Features

Feature requests are welcome! Please:

- **Check existing issues** to avoid duplicates
- **Describe the feature** clearly with use cases
- **Explain why** it would be useful
- **Consider alternatives** you've thought about

### Pull Requests

1. **Fork the repository** and create a feature branch

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Install development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

3. **Make your changes**

   - Write clear, documented code
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests and linters**

   ```bash
   pytest
   black ollama_sgpt tests
   ruff check ollama_sgpt tests
   mypy ollama_sgpt
   ```

5. **Commit your changes**

   - Use clear, descriptive commit messages
   - Follow conventional commits format when possible

   ```
   feat: add multi-model comparison support
   fix: resolve timeout issue in streaming
   docs: update installation instructions
   ```

6. **Push and create a PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Provide a clear description of changes
   - Reference related issues
   - Include screenshots/examples if applicable

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Ollama installed and running
- Git

### Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ollama-sgpt.git
cd ollama-sgpt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Code Style

- **Python**: Follow PEP 8, enforced by Black (line length: 100)
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings for public APIs
- **Imports**: Organize imports (use `ruff` for sorting)

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Test both success and error cases
- Use fixtures from `tests/conftest.py`

Example test:

```python
def test_my_feature(mock_config):
    """Test description."""
    result = my_function(mock_config)
    assert result == expected_value
```

## Documentation

- Update README.md if adding user-facing features
- Add docstrings to new functions and classes
- Update CHANGELOG.md under [Unreleased]
- Create examples in `examples/` directory if helpful

## Project Structure

```
ollama-sgpt/
├── ollama_sgpt/          # Main package
│   ├── cli.py           # CLI interface
│   ├── config.py        # Configuration management
│   ├── history.py       # History persistence
│   ├── ollama_client.py # Ollama API client
│   ├── roles.py         # Role definitions
│   ├── exceptions.py    # Custom exceptions
│   ├── session.py       # Session management
│   └── context.py       # Context handling
├── tests/               # Test suite
├── docs/                # Documentation
└── examples/            # Example configurations
```

## Release Process

Maintainers follow this process for releases:

1. Update version in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish to PyPI

## Questions?

- Open a discussion in GitHub Discussions
- Join our community chat (if available)
- Email the maintainers

Thank you for contributing! 🎉
