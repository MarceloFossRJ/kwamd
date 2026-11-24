# 01: Plugin and skill

Status: ready-for-agent

## Problem

Claude Code agents don't know kwamd exists or how to read its results. See `../spec.md` (stories 1–10, "Layout", "Skill trigger" and "Skill contract").

## Acceptance criteria

- `.claude-plugin/marketplace.json` at the repo root lists one plugin, `kwamd`, pointing at a plugin folder in this repo.
- That plugin has a `.claude-plugin/plugin.json` and a `skills/kwamd/SKILL.md`.
- The skill's description triggers on reading or extracting a PDF's text and on producing a PDF from Markdown.
- The skill body covers every point of the spec's "Skill contract": installed check, Target placement, result path, scanned Source, Markdown → PDF warnings, exit codes 1/2/130 (including the `! kwamd` hand-off for passwords), and no overwrite workarounds.
- The skill uses the GLOSSARY terms (Source, Target, Scanned Source) and doesn't repeat the README beyond what an agent needs to act.
- `/plugin marketplace add <local checkout>` then `/plugin install kwamd` installs it, and the skill shows up in a session outside this repo.
