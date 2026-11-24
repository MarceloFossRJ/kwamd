"""Check docs/specs against the conventions in docs/agents/issue-tracker.md.

- Every feature folder `docs/specs/<feature-slug>/` has a `spec.md`.
- Issue files are named `issues/<NN>-<slug>.md`.
- Every issue file has a `Status:` line with a label from docs/agents/triage-labels.md.

Run from the repo root: `uv run python scripts/check_specs.py`.
"""

import re
import sys
from pathlib import Path

SPECS = Path("docs/specs")
TRIAGE_LABELS = Path("docs/agents/triage-labels.md")
ISSUE_NAME = re.compile(r"^\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.md$")
STATUS_LINE = re.compile(r"^Status:\s*(\S+)\s*$", re.MULTILINE)
# Wayfinder tickets also use `claimed` (see "Wayfinding operations" in issue-tracker.md).
WAYFINDER_LABELS = {"claimed"}


def tracker_labels() -> set[str]:
    """Read the "Label in our tracker" column of the triage-labels table."""
    labels = set()
    for line in TRIAGE_LABELS.read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1].startswith("`") and cells[1].endswith("`"):
            labels.add(cells[1].strip("`"))
    return labels | WAYFINDER_LABELS


def problems() -> list[str]:
    labels = tracker_labels()
    found = []
    for feature in sorted(p for p in SPECS.iterdir() if p.is_dir()):
        if not (feature / "spec.md").is_file():
            found.append(f"{feature}: missing spec.md")
        issues = feature / "issues"
        if not issues.is_dir():
            continue
        for issue in sorted(issues.iterdir()):
            if not ISSUE_NAME.match(issue.name):
                found.append(f"{issue}: name must be <NN>-<slug>.md")
                continue
            match = STATUS_LINE.search(issue.read_text())
            if match is None:
                found.append(f"{issue}: missing a 'Status:' line")
            elif match.group(1) not in labels:
                allowed = ", ".join(sorted(labels))
                found.append(f"{issue}: unknown status '{match.group(1)}' (allowed: {allowed})")
    return found


def main() -> int:
    found = problems()
    for problem in found:
        print(problem, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
