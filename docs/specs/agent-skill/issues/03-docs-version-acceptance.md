# 03: Docs, version 0.3.0 and acceptance run

Status: ready-for-human
Blocked by: 01, 02

## Problem

Users need to learn the skill exists, the release needs its version, and the skill's behaviour can only be checked by hand. See `../spec.md` ("Version", "Docs", "Testing Decisions").

## Acceptance criteria

- The version is 0.3.0 in `pyproject.toml`, the plugin manifest and `uv.lock`, and `scripts/check_plugin.py` passes.
- The README has a "Use from Claude Code" section with the two install commands and what the skill does. If `claude plugin validate` doesn't run in CI, the Development section tells maintainers to run it before a release.
- The six acceptance scenarios in the spec were run in a fresh session outside this repo, and their results are recorded under `## Comments`.

## Comments

- 2026-11-24: Version 0.3.0 and the README section landed on `feat/agent-skill`. `claude plugin validate` runs in CI (it needs no login). The six acceptance scenarios are still to be run by hand; record their results here, then set `Status: resolved`.
