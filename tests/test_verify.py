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


def test_v2_digest_binds_unused_target_suffix():
    # The v1 digest covered only the first len(draft) target tokens on
    # early rejection, although to_dict exposed the entire target sequence.
    left = verify_draft([1], [5, 6], [5, 9, 10])
    right = verify_draft([1], [5, 6], [5, 9, 11])
    assert left.status == right.status == "ACCEPTED_PARTIAL"
    assert left.bonus_token == right.bonus_token == 9
    assert left.accepted_prefix_len == right.accepted_prefix_len == 1
    assert left.receipt_digest != right.receipt_digest


def test_v2_digest_binds_bonus_policy_even_with_no_bonus_token():
    # Both v1 receipts had no bonus, identical visible status and digest,
    # despite different emit_bonus caller policy.
    target = [5, 6]
    enabled = verify_draft([1], [5, 6], target, emit_bonus=True)
    disabled = verify_draft([1], [5, 6], target, emit_bonus=False)
    assert enabled.bonus_token is None and disabled.bonus_token is None
    assert enabled.accepted_prefix_len == disabled.accepted_prefix_len == 2
    assert enabled.receipt_digest != disabled.receipt_digest
    assert enabled.to_dict()["emit_bonus"] is True
    assert disabled.to_dict()["emit_bonus"] is False


def test_v2_deterministic_and_version_label():
    x = verify_draft([7], [3, 4], [3, 9, 8], emit_bonus=True)
    y = verify_draft([7], [3, 4], [3, 9, 8], emit_bonus=True)
    assert x.receipt_digest == y.receipt_digest
    assert x.to_dict()["domain"] == "szl.specdecode.draft-verify.v2"


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
