# Spec: kwamd as a Claude Code agent skill

Status: ready-for-agent

## Problem Statement

I work with Claude Code agents. When I ask one to read a PDF or turn my notes into a PDF, it doesn't know kwamd exists. It reaches for some other approach, or runs kwamd without understanding what kwamd tells it. For example, it might guess the Target path when kwamd actually wrote `report (1).md`, or summarise a Scanned Source as if the near-empty Markdown were the whole document. I want any Claude Code agent, in any project, to use kwamd correctly and honestly.

## Solution

A Claude Code **skill** that teaches the agent to use the existing `kwamd` CLI, shipped as a plugin from this repository. It adds no MCP server, no new runtime, and no change to how kwamd converts files. Every conversion still writes a Target (see `GLOSSARY.md`).

The repository becomes a Claude Code plugin marketplace with one plugin, `kwamd`, which holds the skill. A user installs it once:

```
/plugin marketplace add MarceloFossRJ/kwamd
/plugin install kwamd
```

## User Stories

1. As a user, I want to ask an agent to read, summarise or quote a PDF and have it use kwamd, so that I get kwamd's conversion and not an ad-hoc one.
2. As a user, I want to ask an agent to make a PDF from a Markdown file and have it use kwamd, so that I get kwamd's fixed look.
3. As a user, I want an agent that converts a PDF only to read it to leave nothing behind in my project, so that my working tree stays clean.
4. As a user, I want an agent that I asked for a file to put the Target where I said, or at kwamd's default, and tell me the path kwamd printed.
5. As a user, I want the agent to use the path kwamd prints and never guess it, so that `report (1).md` is read instead of a stale `report.md`.
6. As a user, I want the agent to tell me when a PDF looks scanned and its Markdown may be nearly empty (no OCR), and not present it as the document's content.
7. As a user, I want the agent to pass on kwamd's image and link warnings from Markdown to PDF, and still tell me the PDF was written.
8. As a user, I want the agent to never ask for or handle a PDF password. For a password-protected Source it tells me to run `! kwamd <file>` myself, which gives me the terminal prompt.
9. As a user, I want the agent to tell me how to install kwamd when it's missing, and not install anything itself.
10. As a user, I want to install the skill once and have it work in every project.
11. As a maintainer, I want the plugin version to always equal the package version, enforced by a check, so that the skill and the CLI it describes don't drift apart.

## Implementation Decisions

- **Layout.** `.claude-plugin/marketplace.json` at the repo root lists one plugin, `kwamd`. The plugin's files (its `.claude-plugin/plugin.json` and `skills/kwamd/SKILL.md`) live in a folder of their own in this repo. The exact folder is the implementer's choice, recorded in the README.
- **Skill trigger.** The skill's description makes it fire when a task involves reading or extracting the text of a PDF, or producing a PDF from Markdown. It covers both directions.
- **Skill contract.** The skill tells the agent:
  - **Installed check.** Run `command -v kwamd` first. If kwamd is missing, stop and tell the user to install it (`uv tool install .` from a clone, as in the README). Never install it, and never fall back to `uvx` or a network fetch.
  - **Target placement.** If the user wants the file, pass their path or omit the target. If the agent only needs to read the result, pass a target inside the agent's scratch or temp directory.
  - **Result path.** On exit 0, the Target is the single absolute path on stdout. Read that path, never a guessed one.
  - **Scanned Source.** On the scanned-Source warning on stderr, tell the user the PDF looks scanned and the Markdown may be nearly empty because OCR isn't supported, before using any of it.
  - **Markdown → PDF warnings.** Pass image and link warnings on to the user. The PDF was still written.
  - **Exit 1.** Report kwamd's one-line error. If it says the Source is password-protected, tell the user to run `! kwamd <source> [target]` themselves. Never ask for the password and never pass one.
  - **Exit 2.** Usage error. Fix the invocation; don't retry blindly.
  - **Exit 130.** Interrupted. Report it; don't retry.
  - **Overwriting.** kwamd never overwrites a file. Don't delete or rename files to work around that.
- **Version sync.** The `version` in `plugin.json` (and in the marketplace entry, if it carries one) equals `[project].version` in `pyproject.toml`. A new `scripts/check_plugin.py` checks that the version matches and that both manifests parse as JSON with the fields Claude Code requires. It runs as a pre-commit hook and in CI, next to the spec checks. If `claude plugin validate` can run in CI, it runs there too; if not, the README tells maintainers to run it before a release.
- **Version.** This feature releases kwamd **0.3.0**: `pyproject.toml`, the plugin manifest and `uv.lock`.
- **Docs.** The README gains a "Use from Claude Code" section with the two install commands and a sentence on what the skill does.

## Testing Decisions

- `scripts/check_plugin.py` gets tests in `tests/`, in the style of the spec-check tests: matching versions pass, a mismatch fails naming both versions, and missing or unparseable manifests fail.
- The skill's behaviour is checked by hand. These **acceptance scenarios** run in a fresh Claude Code session with the plugin installed from a local checkout, working in a folder other than this repo:
  1. "Summarise `<a text PDF>`": the agent runs kwamd with a scratch target, reads the printed path, summarises, and leaves no `.md` in the working folder.
  2. "Convert `<a text PDF>` to Markdown here": the agent writes the Target at kwamd's default and reports the printed path. Run it twice: the second time it reports `… (1).md`.
  3. "Make a PDF from `notes.md`" with a missing image: the agent reports the PDF path and passes on the image warning.
  4. A scanned PDF: the agent says it looks scanned and the result may be nearly empty.
  5. A password-protected PDF: the agent tells the user to run `! kwamd <file>`, and doesn't ask for the password.
  6. kwamd not on `PATH`: the agent stops and gives the install instructions.
- No automated `claude plugin eval` suite for now. It calls a model, so it costs money and gives non-deterministic results in CI.

## Out of Scope

- An MCP server, or support for Claude Desktop, claude.ai or Agent SDK apps.
- Writing the Markdown to stdout instead of a Target.
- Any non-interactive password channel (e.g. `--password-stdin`).
- Changes to conversion or rendering.

## Issues

- [01: Plugin and skill](issues/01-plugin-and-skill.md)
- [02: Plugin version check](issues/02-plugin-version-check.md)
- [03: Docs, version 0.3.0 and acceptance run](issues/03-docs-version-acceptance.md)
