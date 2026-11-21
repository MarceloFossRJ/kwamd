# AGENTS.md

## Branches and checks

Start feature work on a `feat/<spec-slug>` branch; `main` changes only through a PR. Run `uv run pre-commit install` once per clone: the hook blocks commits to `main` and runs the same checks as CI. `uv run pre-commit run --all-files` runs them on demand.

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `docs/specs/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
