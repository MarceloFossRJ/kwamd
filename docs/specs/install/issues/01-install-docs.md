# 01: Document how to install kwamd on the PATH

Status: ready-for-agent

## Problem

The README's Usage section shows a bare `kwamd` command, but nothing explains how to get it
on the PATH. After cloning, `kwamd` exists only in `.venv/bin`, so running it from a shell
fails with `command not found` (made worse by the easy typo `kwand`).

## Decisions

- This is an install/documentation gap; the conversion code does not change.
- Supported install: `uv tool install .` (user) and `uv tool install --editable .` (developer).
- No `kwand` alias: `kwamd` is the only command name.
- `uv.lock` stays tracked in git for reproducible installs.

## Acceptance criteria

- README has an Install section before Usage covering install, `uv tool update-shell`,
  reinstall after pulling, and uninstall.
- README Development section mentions `uv tool install --editable .`.
- `.gitignore` does not ignore `uv.lock`.
- After `uv tool install .`, `kwamd --help` (or `kwamd` with no args) runs from outside the repo.
