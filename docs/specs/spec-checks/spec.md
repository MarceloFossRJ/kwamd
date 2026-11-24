# Spec: checks for the docs/specs conventions and .gitignore guards

## Goal

Rules that a script can check are enforced by tooling, not left to review. Two came up while reviewing PR #4:

- `docs/specs/install/` had no `spec.md`, which breaks `docs/agents/issue-tracker.md`.
- A `.gitignore` cleanup stopped ignoring `.pypirc` (PyPI credentials) and `*.log`.

## Scope

- `scripts/check_specs.py`: every feature folder has a `spec.md`; issue files are named `issues/NN-slug.md`; every issue has a `Status:` line with a label from `docs/agents/triage-labels.md`.
- `scripts/check_gitignore.sh`: `.pypirc`, `.env` and `*.log` stay ignored.
- Both run as pre-commit hooks and in CI.
- `resolved` joins the triage labels, so finished issues have a status to move to.

## Issues

- [01: Add spec and .gitignore checks](issues/01-spec-checks.md)
