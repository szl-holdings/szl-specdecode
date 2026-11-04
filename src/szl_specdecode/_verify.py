# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SZL Holdings
"""Lossless draft-then-verify acceptance with SHA3 receipts.

Math silhouette (Leviathan et al.): a draft model proposes K tokens;
the target model scores them in one parallel forward; the longest
prefix that matches the target's greedy (or sampled) continuation is
accepted; one bonus target token may be emitted. Acceptance is lossless
w.r.t. the target distribution when the verify rule matches the target
sampler.

This module implements the *governance* cut: every accept/reject step
emits a digest-bound receipt. It does not ship draft/target weights.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha3_256
from typing import Iterable, List, Optional, Sequence, Tuple
import json

DOMAIN = b"szl.specdecode.draft-verify.v1"


def _canon_ints(xs: Sequence[int]) -> bytes:
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in xs):
        raise TypeError("token ids must be non-bool ints")
    return b",".join(str(int(x)).encode("ascii") for x in xs)


def _digest(*parts: bytes) -> str:
    h = sha3_256()
    h.update(DOMAIN)
    for p in parts:
        h.update(b"\x1f")
        h.update(p)
    return h.hexdigest()


@dataclass(frozen=True)
class DraftVerifyReceipt:
    """One draft-verify round receipt (MEASURED structure, not a GPU claim)."""

    prompt_digest: str
    draft_tokens: Tuple[int, ...]
    target_tokens: Tuple[int, ...]
    accepted_prefix_len: int
    bonus_token: Optional[int]
    receipt_digest: str
    status: str  # ACCEPTED_PARTIAL | ACCEPTED_FULL | REJECTED_ALL

    def to_dict(self) -> dict:
        return {
            "prompt_digest": self.prompt_digest,
            "draft_tokens": list(self.draft_tokens),
            "target_tokens": list(self.target_tokens),
            "accepted_prefix_len": self.accepted_prefix_len,
            "bonus_token": self.bonus_token,
            "receipt_digest": self.receipt_digest,
            "status": self.status,
            "domain": DOMAIN.decode("ascii"),
            "energy": "UNAVAILABLE",
            "speedup_claim": None,
            "credit": "Stephen Lutar",
            "lambda": "Conjecture 1 advisory",
        }


@dataclass
class AcceptanceLedger:
    """Append-only ledger of draft-verify receipts."""

    rounds: List[DraftVerifyReceipt] = field(default_factory=list)

    def append(self, receipt: DraftVerifyReceipt) -> None:
        self.rounds.append(receipt)

    @property
    def mean_accept_len(self) -> Optional[float]:
        if not self.rounds:
            return None
        return sum(r.accepted_prefix_len for r in self.rounds) / len(self.rounds)

    def chain_digest(self) -> str:
        payload = json.dumps([r.to_dict() for r in self.rounds], sort_keys=True, separators=(",", ":"))
        return _digest(b"ledger", payload.encode("utf-8"))


def _require_int_tokens(xs: Sequence[int], *, name: str) -> Tuple[int, ...]:
    out = []
    for i, x in enumerate(xs):
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError(f"{name}[{i}] must be a non-bool int, got {type(x).__name__}")
        out.append(x)
    return tuple(out)


def verify_draft(
    prompt_token_ids: Sequence[int],
    draft_token_ids: Sequence[int],
    target_token_ids: Sequence[int],
    *,
    emit_bonus: bool = True,
) -> DraftVerifyReceipt:
    """Accept the longest draft prefix that equals the target continuation.

    ``target_token_ids`` must be the target model's continuation for the
    same prompt, length >= len(draft) (and +1 if emit_bonus for the bonus
    token after the accepted prefix). This is a CPU reference for the
    lossless accept rule — callers supply both sequences from their models.
    """
    prompt = _require_int_tokens(prompt_token_ids, name="prompt_token_ids")
    draft = _require_int_tokens(draft_token_ids, name="draft_token_ids")
    target = _require_int_tokens(target_token_ids, name="target_token_ids")

    if not draft:
        raise ValueError("draft_token_ids must be non-empty")
    if len(target) < len(draft):
        raise ValueError("target_token_ids must cover the draft length")

    accepted = 0
    for i, tok in enumerate(draft):
        if target[i] == tok:
            accepted += 1
        else:
            break

    bonus: Optional[int] = None
    if emit_bonus:
        # Leviathan: after accepting γ tokens, take the next target token as bonus.
        # If rejected at position j, the target token at j is the recovery token
        # (counted as bonus here for ledger uniformity).
        bonus_index = accepted if accepted < len(draft) else accepted
        if bonus_index < len(target):
            bonus = target[bonus_index]
        elif accepted == len(draft) and len(target) > len(draft):
            bonus = target[len(draft)]

    if accepted == 0:
        status = "REJECTED_ALL"
    elif accepted == len(draft):
        status = "ACCEPTED_FULL"
    else:
        status = "ACCEPTED_PARTIAL"

    prompt_digest = _digest(b"prompt", _canon_ints(prompt))
    receipt_digest = _digest(
        b"receipt",
        prompt_digest.encode("ascii"),
        _canon_ints(draft),
        _canon_ints(target[: max(len(draft), (accepted + 1))]),
        str(accepted).encode("ascii"),
        b"" if bonus is None else str(bonus).encode("ascii"),
        status.encode("ascii"),
    )

    return DraftVerifyReceipt(
        prompt_digest=prompt_digest,
        draft_tokens=draft,
        target_tokens=target,
        accepted_prefix_len=accepted,
        bonus_token=bonus,
        receipt_digest=receipt_digest,
        status=status,
    )


def selfcheck() -> dict:
    """Deterministic CPU self-check. No GPU. No speedup claim."""
    prompt = [1, 2, 3]
    # full accept
    r1 = verify_draft(prompt, [10, 11, 12], [10, 11, 12, 99])
    assert r1.status == "ACCEPTED_FULL" and r1.accepted_prefix_len == 3
    assert r1.bonus_token == 99
    # partial
    r2 = verify_draft(prompt, [10, 11, 12], [10, 11, 77, 88])
    assert r2.status == "ACCEPTED_PARTIAL" and r2.accepted_prefix_len == 2
    assert r2.bonus_token == 77
    # reject all
    r3 = verify_draft(prompt, [10, 11], [20, 21, 22])
    assert r3.status == "REJECTED_ALL" and r3.accepted_prefix_len == 0
    assert r3.bonus_token == 20
    # digests stable
    r1b = verify_draft(prompt, [10, 11, 12], [10, 11, 12, 99])
    assert r1.receipt_digest == r1b.receipt_digest
    ledger = AcceptanceLedger()
    for r in (r1, r2, r3):
        ledger.append(r)
    return {
        "ok": True,
        "rounds": 3,
        "mean_accept_len": ledger.mean_accept_len,
        "chain_digest": ledger.chain_digest(),
        "path": "cpu_reference",
        "gpu_kernel": "UNAVAILABLE",
        "speedup_claim": None,
        "energy": "UNAVAILABLE",
        "credit": "Stephen Lutar",
        "doctrine": "v11",
        "lambda": "Conjecture 1 advisory",
    }
