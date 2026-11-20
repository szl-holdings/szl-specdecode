"""Source-only regression: exactly one gated PyPI publishing entry point.

No credentials, provider calls, releases, or publication occur during these tests.
The controls are structural and do not prove the owner's PyPI OIDC registration.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CANONICAL = WORKFLOWS / "publish-pypi.yml"
PUBLISH_ACTION = re.compile(
    r"(?m)^\s*-\s*name:\s*Publish to PyPI\s*$"
    r"|^\s*uses:\s*pypa/gh-action-pypi-publish@",
)


def _publishing_workflows():
    results = []
    for path in sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml")):
        body = path.read_text(encoding="utf-8")
        if "pypa/gh-action-pypi-publish@" in body:
            results.append(path.name)
    return results


def test_exactly_one_publishing_workflow_and_no_legacy_path():
    assert CANONICAL.is_file()
    assert _publishing_workflows() == ["publish-pypi.yml"]
    assert not (WORKFLOWS / "pypi-publish.yml").exists()


def test_only_release_event_admits_canonical_publish_job():
    body = CANONICAL.read_text(encoding="utf-8")
    assert "release:\n    types: [published]" in body
    assert "workflow_dispatch:" not in body
    assert re.search(r"(?m)^  publish:\s*$", body)
    assert re.search(r"(?m)^    needs: build\s*$", body)
    assert re.search(
        r"(?m)^    if: github\.event_name == 'release'\s*$", body
    )
    assert "python .github/scripts/szl_pypi_release_gate.py" in body


def test_canonical_publish_bound_to_protected_oidc_environment_and_pins():
    body = CANONICAL.read_text(encoding="utf-8")
    publish = body.split("\n  publish:\n", 1)[1]
    assert re.search(r"(?m)^    environment:\s*\n      name: pypi\s*$", publish)
    assert re.search(r"(?m)^      id-token: write\b", publish)
    assert "pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086" in publish
    assert "skip-existing: false" in publish
    assert "verify-metadata: true" in publish
    assert "attestations: true" in publish
    assert "pypa/gh-action-pypi-publish@release/v1" not in body
    assert "uses: actions/checkout@v4" not in body
