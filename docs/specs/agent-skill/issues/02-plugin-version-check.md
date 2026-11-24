# 02: Plugin version check

Status: resolved
Blocked by: 01

## Problem

The plugin's version can drift from the package version, and the skill would then describe a CLI that doesn't match. See `../spec.md` (story 11, "Version sync").

## Acceptance criteria

- `scripts/check_plugin.py` fails, naming both versions, when the `plugin.json` version (or the marketplace entry's version, if present) differs from `[project].version` in `pyproject.toml`.
- It fails with a one-line message when either manifest is missing, isn't valid JSON, or lacks a field Claude Code requires.
- It runs as a pre-commit hook and in CI, alongside the spec checks.
- Tests in `tests/` cover a match, a mismatch, a missing manifest and an unparseable manifest.
- If `claude plugin validate` can run in CI, it runs there. If not, the issue records why under `## Comments`.
