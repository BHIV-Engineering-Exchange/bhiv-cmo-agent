# Hariom Upadhyay — Remediation Changelog (`hariom/cmo-v2-remediation`)

All changes reside **only** in `bhiv-cmo-agent-hariom-remediation` (`hariom/cmo-v2-remediation` from `916022d6`). Original `bhiv-cmo-agent` (`main`) is untouched.

1. **`src/evidence_rag/chunking.py`** *(DQ-002)*: Eliminates duplicate title-only chunks and mid-word overlap cuts (`22` -> `20` marketing chunks when rebuilt).
2. **`src/evidence_rag/evidence.py` & `workflow.py`** *(AC-2)*: Claim-level `validate_claim_citation(..., require_quote=True)`, `top_k=8` proposal retrieval, verbatim quotes, and `2.4%` CTR attribution guard.
3. **`src/evidence_rag/freshness.py` & `workflow.py` Stage 2b** *(DQ-004 — RATIFIED for Local/Staging)*: 48h freshness SLA under `cmo.market_intelligence.v2` (`ds-cmo-marketing-001`), explicit static benchmark exemption (never inferred), and `FRESHNESS_STALE_REVIEW_REQUIRED` flagging in `workflow.py`.
4. **`src/evidence_rag/workflow.py` Stage 5 & 6** *(DQ-005 — RATIFIED)*: 3-tier influencer budget conflict handling (`<= $10,000` proceed; `$10,000.01..$25,000` `CONFLICT_DETECTED` citing both `DOC-MKT-002` & `DOC-MKT-004`; `> $25,000` hard violation `REJECT`). Both corpus documents retained unmodified.
5. **`docs/proposals/cmo_provenance_metadata.schema.json` & `marketing_manifest_provenance_example.json`** *(DQ-003)*: Updated to `CMO_DOMAIN_RATIFIED_MDU_REGISTRATION_PENDING`.
6. **`scripts/evaluate_cmo_marketing_reproducible.py` & `evaluation/results/cmo_marketing_reproducible_benchmark.json`**: Reproducible 14-query replacement benchmark.
7. **Regression Tests:** `tests/unit/test_chunking.py`, `tests/unit/test_freshness_validation.py`, `tests/regression/test_ac2_semantic_grounding.py`, `tests/regression/test_dq005_influencer_boundaries.py`.
