# Shell Benchmarks

This directory contains the `v0.3` shell benchmark suite, the runner used to score it, and the committed baseline output.

## Files

- `shell_suite.json`: benchmark inputs for deterministic extraction/safety scoring and live shell-generation checks
- `baselines/v0.3-shell-baseline.json`: the committed benchmark baseline
- `../scripts/benchmarks/run_shell_benchmarks.py`: the benchmark runner

## What Gets Measured

- command extraction accuracy from model-style shell responses
- safety classification accuracy, including false positives and false negatives
- live shell command accuracy against local Ollama models
- average and p95 latency for each benchmarked model class

## Run The Benchmark

From the repository root:

```bash
python scripts/benchmarks/run_shell_benchmarks.py
```

Optional flags:

```bash
python scripts/benchmarks/run_shell_benchmarks.py --skip-live
python scripts/benchmarks/run_shell_benchmarks.py --models gpt-oss:20b,qwen3-coder:30b
python scripts/benchmarks/run_shell_benchmarks.py --output benchmarks/baselines/custom-run.json
```

## Current Baseline

The current `v0.3` baseline was captured on `2026-03-31` against local Ollama models and is committed in `baselines/v0.3-shell-baseline.json`.

- Deterministic extraction fixtures: `4/4` passed (`100%`)
- Deterministic safety fixtures: `9/9` exact matches (`100%`), with `0` false positives and `0` false negatives
- Live shell generation:
  - `gpt-oss:20b` (`general-local`): `6/6` passed (`100%`), average latency `16021.79 ms`, p95 `28049.56 ms`
  - `qwen3-coder:30b` (`code-local`): `6/6` passed (`100%`), average latency `3865.87 ms`, p95 `17080.41 ms`

The baseline should be regenerated whenever shell extraction rules, safety classification behavior, or the benchmark suite itself changes.
