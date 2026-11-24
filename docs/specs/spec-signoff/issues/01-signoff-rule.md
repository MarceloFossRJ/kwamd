# 01: Add the sign-off rule to the coding standards

Status: ready-for-agent

## Problem

Nothing stops an implementation PR from rewriting a recorded decision to match the code. See `../spec.md`.

## Acceptance criteria

- `CODING_STANDARDS.md` has a "Specs and decisions" section with the rule as the spec states it: approval named in the commit message; added detail and newly made decisions exempt; docs edited to match code without approval is a hard violation.
- No other file restates the rule.
