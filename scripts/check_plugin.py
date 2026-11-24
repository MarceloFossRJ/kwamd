"""Check the Claude Code plugin manifests against pyproject.toml.

The plugin's version must equal the package's, so the skill never describes a
different kwamd from the one it ships with (docs/specs/agent-skill/spec.md).
"""

import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_JSON = "plugins/kwamd/.claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
PLUGIN_NAME = "kwamd"


def load(root: Path, manifest: str, found: list[str]) -> dict[str, Any] | None:
    """Read one manifest, or record why it can't be read and return None."""
    path = root / manifest
    if not path.is_file():
        found.append(f"{manifest}: missing")
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        found.append(f"{manifest}: not valid JSON ({error})")
        return None
    if not isinstance(data, dict):
        found.append(f"{manifest}: not a JSON object")
        return None
    return data


def require(
    manifest: str, data: dict[str, Any], fields: list[str], found: list[str], prefix: str = ""
) -> None:
    """Record each dotted field (``owner.name``) that is absent or empty."""
    for dotted in fields:
        value: Any = data
        for key in dotted.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if value in (None, "", {}):
            found.append(f"{manifest}: missing required field '{prefix}{dotted}'")


def check_marketplace(marketplace: dict[str, Any], package_version: str, found: list[str]) -> None:
    """Check the marketplace's required fields and its entry for PLUGIN_NAME."""
    require(MARKETPLACE_JSON, marketplace, ["name", "owner.name"], found)
    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        found.append(f"{MARKETPLACE_JSON}: missing required field 'plugins'")
        return
    listed = False
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            found.append(f"{MARKETPLACE_JSON}: plugins[{index}] is not a JSON object")
            continue
        require(MARKETPLACE_JSON, entry, ["name", "source"], found, prefix=f"plugins[{index}].")
        if entry.get("name") == PLUGIN_NAME:
            listed = True
            check_version(
                f"{MARKETPLACE_JSON}: plugin '{PLUGIN_NAME}'", entry, package_version, found
            )
    if not listed:
        found.append(f"{MARKETPLACE_JSON}: does not list the '{PLUGIN_NAME}' plugin")


def check_version(where: str, data: dict[str, Any], package_version: str, found: list[str]) -> None:
    """Record a ``version`` in ``data`` that differs from the package's (absent is fine)."""
    version = data.get("version")
    if version not in (None, "") and version != package_version:
        found.append(
            f"{where} version {version} does not match pyproject.toml version {package_version}"
        )


def breaches(root: Path) -> list[str]:
    """One message per way the plugin manifests break the rules."""
    package_version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    found: list[str] = []
    plugin = load(root, PLUGIN_JSON, found)
    marketplace = load(root, MARKETPLACE_JSON, found)
    if plugin is not None:
        require(PLUGIN_JSON, plugin, ["name", "version"], found)
        check_version(f"{PLUGIN_JSON}:", plugin, package_version, found)
    if marketplace is not None:
        check_marketplace(marketplace, package_version, found)
    return found


def main() -> int:
    found = breaches(ROOT)
    for breach in found:
        print(breach, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
