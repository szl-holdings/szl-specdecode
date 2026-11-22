"""Source-only contract: one protected PyPI release writer for this repository.

No credential, provider write, GitHub Release, or package publication occurs
during these tests. Static checks do not authenticate PyPI OIDC registration.
"""
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CANONICAL = WORKFLOWS / "publish-pypi.yml"
# Look for alternate upload tools, not only the canonical pypa Action. This is
# a conservative source gate: newly introduced publication code needs review.
PUBLISH_INDICATOR = re.compile(
    r"(?i)(?:pypa/gh-action-pypi-publish@"
    r"|\b(?:python\s+-m\s+)?twine\s+upload\b"
    r"|\buv\s+publish\b|\bpoetry\s+publish\b"
    r"|\bhatch\s+publish\b|pypi\.org/legacy)"
)


def _publishing_workflows(directory=WORKFLOWS):
    found = []
    paths = list(directory.glob("*.yml")) + list(directory.glob("*.yaml"))
    for path in sorted(paths):
        # Count occurrences, not filenames: two publish actions inside one
        # workflow are still two independent release writers.
        matches = list(PUBLISH_INDICATOR.finditer(path.read_text(encoding="utf-8")))
        found.extend([path.name] * len(matches))
    return found


def _require_single_publisher(directory=WORKFLOWS):
    publishers = _publishing_workflows(directory)
    if publishers != ["publish-pypi.yml"]:
        raise AssertionError("ALTERNATE_PYPI_PUBLISHER: " + ",".join(publishers))


def _canonical_release_contract(body):
    return all((
        "release:\n    types: [published]" in body,
        "workflow_dispatch:" not in body,
        re.search(r"(?m)^  publish:\s*$", body) is not None,
        re.search(r"(?m)^    needs: build\s*$", body) is not None,
        re.search(r"(?m)^    if: github\.event_name == 'release'\s*$", body) is not None,
        "python .github/scripts/szl_pypi_release_gate.py" in body,
        "pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086" in body,
        "pypa/gh-action-pypi-publish@release/v1" not in body,
        "uses: actions/checkout@v4" not in body,
    ))


def test_exactly_one_publishing_workflow_and_no_legacy_path():
    assert CANONICAL.is_file()
    _require_single_publisher()
    assert not (WORKFLOWS / "pypi-publish.yml").exists()


def test_only_release_event_admits_canonical_publish_job():
    body = CANONICAL.read_text(encoding="utf-8")
    assert _canonical_release_contract(body)


def test_canonical_publish_bound_to_protected_oidc_environment():
    body = CANONICAL.read_text(encoding="utf-8")
    publish = body.split("\n  publish:\n", 1)[1]
    assert re.search(r"(?m)^    environment:\s*\n      name: pypi\s*$", publish)
    assert re.search(r"(?m)^      id-token: write\b", publish)
    for value in ("skip-existing: false", "verify-metadata: true", "attestations: true"):
        assert value in publish


@pytest.mark.parametrize("alt", [
    "run: python -m twine upload dist/*.whl",
    "run: uv publish",
    "run: poetry publish",
    "run: hatch publish",
    "uses: pypa/gh-action-pypi-publish@release/v1",
])
def test_extra_release_writer_fails_without_provider_call(tmp_path, alt):
    # A forged second workflow must be detected even if it avoids the
    # exact official pypa publish action string used in the original test.
    (tmp_path / CANONICAL.name).write_text(
        CANONICAL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "alternate.yml").write_text(
        "on:\n  release:\n    types: [published]\njobs:\n"
        "  bypass:\n    steps:\n      - " + alt + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="ALTERNATE_PYPI_PUBLISHER"):
        _require_single_publisher(tmp_path)


def test_second_publish_action_inside_canonical_workflow_is_rejected(tmp_path):
    body = CANONICAL.read_text(encoding="utf-8")
    publisher = next(
        line for line in body.splitlines()
        if "uses: pypa/gh-action-pypi-publish@" in line
    )
    mutated = body.replace(publisher, publisher + "\n" + publisher, 1)
    (tmp_path / CANONICAL.name).write_text(mutated, encoding="utf-8")
    with pytest.raises(AssertionError, match="ALTERNATE_PYPI_PUBLISHER"):
        _require_single_publisher(tmp_path)


def test_manual_dispatch_and_unconditional_publish_bypass_are_rejected():
    body = CANONICAL.read_text(encoding="utf-8")
    assert not _canonical_release_contract(body + "\nworkflow_dispatch: {}\n")
    assert not _canonical_release_contract(
        body.replace(
            "    if: github.event_name == 'release'",
            "    if: always()",
        )
    )
