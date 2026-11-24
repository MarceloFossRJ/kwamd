"""scripts/check_plugin.py: the plugin's version follows the package's."""

import json
from pathlib import Path
from typing import Any

from check_plugin import breaches

PLUGIN_JSON = "plugins/kwamd/.claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"


def make_repo(
    root: Path,
    *,
    package_version: str = "1.2.3",
    plugin: dict[str, Any] | None = None,
    marketplace: dict[str, Any] | None = None,
) -> Path:
    """Write a minimal repo with a pyproject, a marketplace and one plugin."""
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "kwamd"\nversion = "{package_version}"\n'
    )
    write_json(root / PLUGIN_JSON, plugin or {"name": "kwamd", "version": package_version})
    write_json(
        root / MARKETPLACE_JSON,
        marketplace
        or {
            "name": "kwamd",
            "owner": {"name": "Someone"},
            "plugins": [{"name": "kwamd", "source": "./plugins/kwamd"}],
        },
    )
    return root


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_matching_versions_pass(tmp_path: Path) -> None:
    assert breaches(make_repo(tmp_path)) == []


def test_plugin_version_differing_from_package_fails_naming_both(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, plugin={"name": "kwamd", "version": "1.2.2"})
    assert breaches(repo) == [
        f"{PLUGIN_JSON}: version 1.2.2 does not match pyproject.toml version 1.2.3"
    ]


def test_missing_plugin_manifest_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / PLUGIN_JSON).unlink()
    assert breaches(repo) == [f"{PLUGIN_JSON}: missing"]


def test_missing_marketplace_manifest_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / MARKETPLACE_JSON).unlink()
    assert breaches(repo) == [f"{MARKETPLACE_JSON}: missing"]


def test_unparseable_manifest_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / PLUGIN_JSON).write_text('{"name": "kwamd",')
    [breach] = breaches(repo)
    assert breach.startswith(f"{PLUGIN_JSON}: not valid JSON (")


def test_manifest_that_is_not_an_object_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / MARKETPLACE_JSON).write_text("[]")
    assert breaches(repo) == [f"{MARKETPLACE_JSON}: not a JSON object"]


def test_plugin_manifest_without_a_version_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, plugin={"name": "kwamd"})
    assert breaches(repo) == [f"{PLUGIN_JSON}: missing required field 'version'"]


def test_marketplace_without_required_fields_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, marketplace={"plugins": [{"name": "kwamd"}]})
    assert breaches(repo) == [
        f"{MARKETPLACE_JSON}: missing required field 'name'",
        f"{MARKETPLACE_JSON}: missing required field 'owner.name'",
        f"{MARKETPLACE_JSON}: missing required field 'plugins[0].source'",
    ]


def test_marketplace_not_listing_the_plugin_fails(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        marketplace={"name": "kwamd", "owner": {"name": "Someone"}, "plugins": []},
    )
    assert breaches(repo) == [f"{MARKETPLACE_JSON}: does not list the 'kwamd' plugin"]


def test_marketplace_entry_version_differing_from_package_fails(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        marketplace={
            "name": "kwamd",
            "owner": {"name": "Someone"},
            "plugins": [{"name": "kwamd", "source": "./plugins/kwamd", "version": "0.0.1"}],
        },
    )
    assert breaches(repo) == [
        f"{MARKETPLACE_JSON}: plugin 'kwamd' version 0.0.1 does not match "
        "pyproject.toml version 1.2.3"
    ]


def test_every_breach_is_reported_together(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        plugin={"name": "kwamd", "version": "9.9.9"},
        marketplace={"name": "kwamd", "owner": {"name": "Someone"}, "plugins": []},
    )
    assert breaches(repo) == [
        f"{PLUGIN_JSON}: version 9.9.9 does not match pyproject.toml version 1.2.3",
        f"{MARKETPLACE_JSON}: does not list the 'kwamd' plugin",
    ]
