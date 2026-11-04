# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SZL Holdings
from szl_specdecode import verify_draft, selfcheck, AcceptanceLedger


def test_full_accept_with_bonus():
    r = verify_draft([1], [5, 6], [5, 6, 7])
    assert r.status == "ACCEPTED_FULL"
    assert r.accepted_prefix_len == 2
    assert r.bonus_token == 7
    assert len(r.receipt_digest) == 64


def test_partial_and_reject():
    assert verify_draft([1], [5, 6, 7], [5, 9, 9]).accepted_prefix_len == 1
    assert verify_draft([1], [5, 6], [8, 9]).status == "REJECTED_ALL"


def test_rejects_non_int_tokens():
    try:
        verify_draft([1.0], [2], [2])  # type: ignore[list-item]
        assert False, "expected TypeError"
    except TypeError:
        pass


def test_selfcheck():
    out = selfcheck()
    assert out["ok"] is True
    assert out["gpu_kernel"] == "UNAVAILABLE"
    assert out["speedup_claim"] is None
    assert out["energy"] == "UNAVAILABLE"


def test_ledger_chain_stable():
    led = AcceptanceLedger()
    led.append(verify_draft([1], [2], [2, 3]))
    a = led.chain_digest()
    b = led.chain_digest()
    assert a == b
