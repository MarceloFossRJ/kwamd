# 01: Add spec and .gitignore checks

Status: resolved

## Problem

Two mechanical rules were caught only in code review (see `../spec.md`). Commits that touch only docs skip every pre-commit hook, because all of them are `types: [python]`.

## Acceptance criteria

- `uv run python scripts/check_specs.py` exits 1 when a feature folder has no `spec.md`, when an issue file is misnamed, or when its `Status:` is missing or unknown, and exits 0 on the current tree.
- `scripts/check_gitignore.sh` exits 1 if `.pypirc`, `.env` or `debug.log` is no longer ignored.
- Both run in pre-commit and in CI.
- `resolved` is a triage label, and `01-install-docs.md` uses it.
