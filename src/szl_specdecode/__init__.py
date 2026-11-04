# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 SZL Holdings
"""SZL speculative decoding silhouette — draft-then-verify with receipts.

Inspired by Leviathan et al. speculative decoding (arXiv:2211.17192).
NOT a rehost of Medusa, EAGLE, TensorRT-LLM, vLLM, or Modular MAX.
CPU reference only. No speedup claim. No GPU kernel claim.
"""

from ._verify import (
    DraftVerifyReceipt,
    AcceptanceLedger,
    verify_draft,
    selfcheck,
)

__all__ = [
    "DraftVerifyReceipt",
    "AcceptanceLedger",
    "verify_draft",
    "selfcheck",
]
__version__ = "0.1.0"
