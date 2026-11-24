# Spec: sign-off before a recorded decision changes

Status: ready-for-agent

## Problem

Specs, issues and ADRs record decisions the user made. During implementation it is tempting to edit them so they describe what the code now does. In #7 an implementation commit rewrote the spec's image decision, from "served through an archive of the Source's folder" to "`../` and absolute paths allowed", to match the code. Only the spec reviewer caught it, and the user then made the call. A quiet edit like that turns a review into a rubber stamp: the docs agree with the code because they were changed to.

## Solution

A judgement rule in `CODING_STANDARDS.md`, under a new "Specs and decisions" section, for the reviewer to apply:

- A PR that changes a decision already recorded in a spec, issue or ADR (scope, a rule, an option it rejected) names the user's approval in the commit message that makes the edit.
- Adding detail inside an agreed decision, or recording a decision the user just made, needs nothing extra.
- Editing the docs to match the code without an approval is a hard violation; the code changes instead, or the user decides.

## Decisions

- **A rule for the reviewer, not a check.** Telling a clarification from a changed decision needs judgement, so it lives in `CODING_STANDARDS.md`, which is read during review.
- **The approval goes in the commit message.** Reviewers see the diff and the commits, not the PR description, so that is where they can check it. Review prompts include full commit messages, not just subject lines.
- **A missing approval is a hard violation,** not a judgement call: the rule exists because the failure is easy to miss and costly.

## Out of scope

- An automated check that spec files change only alongside an approval line.
- Changing how decisions are recorded (spec format, ADR format).

## Issues

- [01: Add the sign-off rule to the coding standards](issues/01-signoff-rule.md)
