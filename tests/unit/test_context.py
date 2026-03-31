"""Tests for context management."""
import pytest
from ollama_sgpt.context import (
    load_context_files,
    build_context_prompt,
    format_context_summary,
    validate_context_files
)


@pytest.fixture
def sample_files(tmp_path):
    """Create sample context files."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("This is file 1 content")

    file2 = tmp_path / "file2.txt"
    file2.write_text("This is file 2 content")

    return [str(file1), str(file2)]


def test_load_context_files(sample_files):
    """Test loading multiple context files."""
    context = load_context_files(sample_files)

    assert "file1.txt" in context
    assert "file2.txt" in context
    assert "This is file 1 content" in context
    assert "This is file 2 content" in context
    assert "--- File:" in context


def test_load_context_files_not_found(tmp_path):
    """Test that loading a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_context_files([str(tmp_path / "nonexistent.txt")])


def test_load_context_files_unreadable(tmp_path):
    """Test handling of unreadable files."""
    file = tmp_path / "unreadable.txt"
    file.write_text("content")

    # Make file unreadable (Unix-like systems)
    import os
    if os.name != 'nt':  # Skip on Windows
        file.chmod(0o000)

        with pytest.raises(IOError):
            load_context_files([str(file)])

        # Clean up
        file.chmod(0o644)


def test_load_context_files_empty_list():
    """Test loading an empty list of files."""
    context = load_context_files([])
    assert context == ""


def test_build_context_prompt_with_context():
    """Test building a prompt with context."""
    user_input = "What does this code do?"
    context = "def hello():\n    print('Hello')"

    prompt = build_context_prompt(user_input, context)

    assert "Context information:" in prompt
    assert "def hello():" in prompt
    assert "What does this code do?" in prompt
    assert "Based on the context above" in prompt


def test_build_context_prompt_without_context():
    """Test building a prompt without context."""
    user_input = "Hello world"

    prompt = build_context_prompt(user_input, None)

    assert prompt == "Hello world"
    assert "Context information:" not in prompt


def test_build_context_prompt_empty_context():
    """Test building a prompt with empty context."""
    user_input = "Hello"

    prompt = build_context_prompt(user_input, "")

    # Empty string is falsy, so should return just user_input
    assert prompt == "Hello"


def test_format_context_summary_no_files():
    """Test formatting summary with no files."""
    summary = format_context_summary([])
    assert summary == "No context files loaded"


def test_format_context_summary_with_files(sample_files):
    """Test formatting summary with multiple files."""
    summary = format_context_summary(sample_files)

    assert "Loaded 2 context file(s)" in summary
    assert "file1.txt" in summary
    assert "file2.txt" in summary
    assert "bytes" in summary


def test_format_context_summary_missing_file(tmp_path):
    """Test formatting summary with a missing file."""
    missing_file = str(tmp_path / "missing.txt")
    summary = format_context_summary([missing_file])

    assert "missing.txt" in summary
    assert "not found" in summary


def test_validate_context_files_all_valid(sample_files):
    """Test validating all valid files."""
    valid, invalid = validate_context_files(sample_files)

    assert len(valid) == 2
    assert len(invalid) == 0
    assert sample_files[0] in valid
    assert sample_files[1] in valid


def test_validate_context_files_some_invalid(tmp_path):
    """Test validating with some invalid files."""
    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("content")

    missing_file = tmp_path / "missing.txt"

    files = [str(valid_file), str(missing_file)]
    valid, invalid = validate_context_files(files)

    assert len(valid) == 1
    assert len(invalid) == 1
    assert str(valid_file) in valid
    assert str(missing_file) in invalid


def test_validate_context_files_all_invalid(tmp_path):
    """Test validating all invalid files."""
    files = [
        str(tmp_path / "missing1.txt"),
        str(tmp_path / "missing2.txt")
    ]

    valid, invalid = validate_context_files(files)

    assert len(valid) == 0
    assert len(invalid) == 2


def test_validate_context_files_directory(tmp_path):
    """Test that directories are considered invalid."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    valid, invalid = validate_context_files([str(subdir)])

    assert len(valid) == 0
    assert len(invalid) == 1


def test_load_context_files_preserves_order(tmp_path):
    """Test that files are loaded in the order provided."""
    file1 = tmp_path / "first.txt"
    file1.write_text("First")

    file2 = tmp_path / "second.txt"
    file2.write_text("Second")

    context = load_context_files([str(file1), str(file2)])

    # Check that "First" appears before "Second" in the context
    first_pos = context.find("First")
    second_pos = context.find("Second")

    assert first_pos < second_pos


def test_load_context_files_with_unicode(tmp_path):
    """Test loading files with Unicode content."""
    file = tmp_path / "unicode.txt"
    file.write_text("Hello 世界 🌍", encoding='utf-8')

    context = load_context_files([str(file)])

    assert "Hello 世界 🌍" in context


def test_load_context_files_large_file(tmp_path):
    """Test loading a large file."""
    file = tmp_path / "large.txt"
    content = "Line\n" * 10000  # 10,000 lines
    file.write_text(content)

    context = load_context_files([str(file)])

    assert "Line" in context
    assert content in context
