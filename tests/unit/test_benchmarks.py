"""Tests for benchmark helper functions."""

from ollama_sgpt.benchmarks import (
    command_matches_expected,
    percentile,
    summarize_extraction_cases,
    summarize_safety_cases,
)


def test_command_matches_expected_uses_regex_patterns():
    """Expected command regexes should match accepted command variants."""
    patterns = [r"^Get-ChildItem\b(?=.*-Recurse\b)(?=.*-Filter\s+\*\.py).*$"]

    assert command_matches_expected(
        "Get-ChildItem -Path . -Recurse -Filter *.py",
        patterns,
    ) is True


def test_command_matches_expected_accepts_semantic_option_reordering():
    """Equivalent shell commands should pass even when option order differs."""
    patterns = [
        r"^find\s+\.\s+-type\s+f\s+-name\s+['\"]?\*\.py['\"]?$",
        r"^find\s+\.\s+-name\s+['\"]?\*\.py['\"]?(?:\s+-type\s+f)?$",
    ]

    assert command_matches_expected(
        'find . -name "*.py" -type f',
        patterns,
    ) is True


def test_percentile_returns_nearest_rank_value():
    """Percentile helper should return the nearest-rank sample value."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    assert percentile(values, 95) == 50.0
    assert percentile(values, 50) == 30.0


def test_summarize_extraction_cases_scores_exact_matches():
    """Extraction summary should count exact command matches."""
    cases = [
        {
            "id": "powershell-code-block",
            "shell": "powershell",
            "response": "```powershell\nPS C:\\Users\\me> Get-ChildItem -Name\n```",
            "expected_command": "Get-ChildItem -Name",
        },
        {
            "id": "cmd-numbered",
            "shell": "cmd",
            "response": "1. Command: dir /s *.py",
            "expected_command": "dir /s *.py",
        },
    ]

    summary = summarize_extraction_cases(cases)

    assert summary["passed_cases"] == 2
    assert summary["accuracy"] == 1.0


def test_summarize_safety_cases_tracks_false_positive_and_negative():
    """Safety summary should count dangerous misses and safe over-classification."""
    cases = [
        {
            "id": "safe-command",
            "shell": "powershell",
            "command": "Get-ChildItem -Name",
            "expected_risk": "high",
        },
        {
            "id": "dangerous-command",
            "shell": "powershell",
            "command": "Remove-Item -LiteralPath C:\\temp -Force -Recurse",
            "expected_risk": "low",
        },
    ]

    summary = summarize_safety_cases(cases)

    assert summary["false_negatives"] == 1
    assert summary["false_positives"] == 1
