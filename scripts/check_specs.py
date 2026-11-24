"""Check docs/specs against the conventions in docs/agents/issue-tracker.md.

Allowed `Status:` labels come from the table in docs/agents/triage-labels.md.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "docs/specs"
TRIAGE_LABELS = ROOT / "docs/agents/triage-labels.md"
ISSUE_NAME = re.compile(r"^(?!00-)[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.md$")
STATUS_LINE = re.compile(r"^Status:\s*(\S+)\s*$", re.MULTILINE)


def tracker_labels() -> set[str]:
    """Read the "Label in our tracker" column of the triage-labels table."""
    labels = set()
    for line in TRIAGE_LABELS.read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1].startswith("`") and cells[1].endswith("`"):
            labels.add(cells[1].strip("`"))
    return labels


def header(text: str) -> str:
    """The part of an issue file before its first `##` section."""
    return re.split(r"^## ", text, maxsplit=1, flags=re.MULTILINE)[0]


def convention_breaches(labels: set[str]) -> list[str]:
    """One message per place docs/specs breaks the issue-tracker conventions."""
    breaches = []
    for feature in sorted(p for p in SPECS.iterdir() if p.is_dir()):
        if not (feature / "spec.md").is_file():
            breaches.append(f"{feature.relative_to(ROOT)}: missing spec.md")
        issues = feature / "issues"
        if not issues.is_dir():
            continue
        for issue in sorted(p for p in issues.glob("*.md") if p.is_file()):
            where = issue.relative_to(ROOT)
            if not ISSUE_NAME.match(issue.name):
                breaches.append(f"{where}: name must be <NN>-<slug>.md, numbered from 01")
                continue
            match = STATUS_LINE.search(header(issue.read_text()))
            if match is None:
                breaches.append(f"{where}: missing a 'Status:' line before the first section")
            elif match.group(1) not in labels:
                allowed = ", ".join(sorted(labels))
                breaches.append(f"{where}: unknown status '{match.group(1)}' (allowed: {allowed})")
    return breaches


def main() -> int:
    labels = tracker_labels()
    if not labels:
        print(f"{TRIAGE_LABELS.relative_to(ROOT)}: found no labels in the table", file=sys.stderr)
        return 1
    breaches = convention_breaches(labels)
    for breach in breaches:
        print(breach, file=sys.stderr)
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
