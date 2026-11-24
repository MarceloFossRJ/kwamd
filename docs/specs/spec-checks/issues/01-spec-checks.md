# 01: Add spec and .gitignore checks

Status: resolved

## Problem

Two mechanical rules were caught only in code review (see `../spec.md`). Commits that touch only docs skip every pre-commit hook, because all of them are `types: [python]`.

## Acceptance criteria

- `uv run python scripts/check_specs.py` exits 1 when a feature folder has no `spec.md`, when an issue file is misnamed, or when the issue's header (before its first `##` section) has no `Status:` line or an unknown one, and exits 0 on the current tree. It works from any folder.
- `scripts/check_gitignore.sh` exits 1 if `.pypirc`, `.env`, `debug.log` or `other.log` is no longer ignored by the repo's `.gitignore` (personal ignore files don't count).
- Both run in pre-commit and in CI.
- `resolved` is a triage label, and `01-install-docs.md` uses it.
