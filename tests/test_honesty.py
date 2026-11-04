# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SZL Holdings
"""Honesty labels. Not a Λ proof. Not a speedup claim."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")

REQUIRED = [
    "Doctrine v11",
    "Conjecture 1",
    "Original SZL construction",
    "https://arxiv.org/abs/2211.17192",
    "NOT a rehost",
    "UNAVAILABLE",
    "Stephen Lutar",
    "MEASURED-or-null",
]


def test_readme_honesty_phrases():
    for phrase in REQUIRED:
        assert phrase in README, f"missing honesty phrase: {phrase}"


def test_no_fabricated_speedup():
    lower = README.lower()
    assert "tokens/s MEASURED" not in README
    assert "x faster than vllm" not in lower
