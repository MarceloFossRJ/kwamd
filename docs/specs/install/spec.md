# Spec: Installing kwamd

## Goal

A person who clones this repository can put the `kwamd` command on their PATH and run it from
any folder, following the README alone.

## Scope

- Documentation only; the conversion behaviour does not change.
- uv is the only supported installer: `uv tool install .` for users, `uv tool install --editable .`
  for development.
- `kwamd` is the only command name; no aliases.

## Out of scope

- Publishing to PyPI or other package indexes.
- Installers other than uv (pipx, pip, Homebrew).

## Issues

- [01: Document how to install kwamd on the PATH](issues/01-install-docs.md)
