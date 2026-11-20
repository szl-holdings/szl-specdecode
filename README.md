# szl-specdecode
<!-- szl:header v1 -->
<!-- Native identity: szl-brand orbit-v2. -->
<p>
  <a href="https://github.com/szl-holdings">
    <img src="https://raw.githubusercontent.com/szl-holdings/szl-brand/4309f6fce89179331b0b3ed8c99494e76c5be256/kit/logos/orbit-v2/suite/szl-icon-32.svg" alt="SZL Holdings — Orbit v2" width="32" height="32" />
  </a>
</p>

**Control before action. Evidence after.**

[Product](https://a-11-oy.com) · [Proof](https://a11oy.net) · [GitHub organization](https://github.com/szl-holdings)
<!-- /szl:header -->

**Original SZL construction in the speculative-decoding category.** Inspired by Leviathan et al. Fast Inference from Transformers via Speculative Decoding https://arxiv.org/abs/2211.17192. **NOT a rehost** of Medusa, EAGLE, TensorRT-LLM speculative decoding, vLLM speculators, Modular MAX, Together, or Fireworks FireOptimizer.

Doctrine v11. **Λ = Conjecture 1 OPEN** (advisory; uniqueness unproven). MEASURED-or-null.

## Status

| Thing | Label | Method / what-NOT |
|---|---|---|
| CPU draft-verify accept rule + SHA3 receipts | **import-LIVE** | `selfcheck()` deterministic; no model weights bundled |
| GPU / fused draft kernels | **UNAVAILABLE** | Not claimed |
| Speedup vs autoregressive | **null** | No tokens/s claim until MEASURED draft/target pair receipt |
| Energy | **UNAVAILABLE** | No meter attached |

## Cookie

Thanks to the authors of speculative decoding, Medusa, EAGLE, NVIDIA TensorRT-LLM, vLLM, Modular MAX, Together, and Fireworks for productizing draft-then-verify. SZL builds a clean-room governance silhouette: acceptance ledgers with SHA3 receipts and honest nulls for speed and joules.

Credit **Stephen Lutar**.

## Quick start

```bash
pip install -e '.[dev]'
python -c 'from szl_specdecode import selfcheck; print(selfcheck())'
pytest -q
```

```python
from szl_specdecode import verify_draft

receipt = verify_draft(
    prompt_token_ids=[1, 2, 3],
    draft_token_ids=[10, 11, 12],
    target_token_ids=[10, 11, 12, 99],  # target continuation (+ bonus)
)
print(receipt.status, receipt.accepted_prefix_len, receipt.receipt_digest[:16])
```

## Receipt format safety (source-only v2 candidate)

The v1 receipt hash omitted unused trailing caller-declared target tokens and
did not bind whether the caller requested bonus emission. Distinct disclosed
receipts could therefore share a digest. This candidate changes the domain to
`szl.specdecode.draft-verify.v2`, hashes the **entire declared target-token
sequence**, and binds the `emit_bonus` policy. v1 and v2 digests are deliberately
**not interchangeable**; existing v1 chains must remain labeled v1, and any
migration requires separate source-owner review and consumer compatibility
tests. This patch is not a package release or runtime promotion.

A SHA3 receipt is *integrity of caller-declared inputs*, not authentication of
the target model, its sampler or its runtime. The equality-based CPU reference
does not implement the probabilistic accept/correct rule needed for general
distribution-preserving sampled speculative decoding; no sampled-mode speed,
distribution or quality claim is established here.

## What this is / is not

- **Is:** lossless accept-prefix rule + append-only `AcceptanceLedger` + digest-bound `DraftVerifyReceipt`.
- **Is not:** a draft model, a target model, a CUDA kernel, a drop-in vLLM replacement, or a fabricated throughput number.

Wire real draft/target models at the call site; keep the receipt.

Estate on Hugging Face: models, datasets and Spaces are published under the [SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS) org.

## License

Apache-2.0 — see [LICENSE](LICENSE).
