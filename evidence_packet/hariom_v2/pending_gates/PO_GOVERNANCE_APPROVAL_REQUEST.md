# Formal Governance Approval Request — Next Integration Step Only

- **To:** `Pratik Bhuwad / Prateek` (CMO Product Owner) & Governance Authority
- **From:** `Hariom Upadhyay` (Data Quality & Evaluation Lead)
- **Repository / Branch:** `bhiv-cmo-agent-hariom-remediation` (`hariom/cmo-v2-remediation` @ `916022d62812358b3aef594e74e9cc2a61901fce`)
- **Patch:** `hariom-cmo-v2-remediation-review-v4.patch` (`127,358` bytes, SHA256: `54FF8D57B001D1EFBD5F37E329C1963121C3CA359A3E817F708AD966711E0265`)
- **Governance Approval:** **NOT RECEIVED** (**PO approval pending**)
- **MDU Schema Registration:** **NOT REGISTERED**
- **Integration Status:** **NOT AUTHORIZED**
- **Requested Scope:** **NEXT INTEGRATION STEP ONLY (Staging / CI Integration)** — **NOT** production deployment, **NOT** live customer/PII data, **NOT** external campaign activation.

## 1. Scope & Remediation Summary (`V4`)
- **DQ-002:** Prevented duplicate heading-only chunks and mid-word overlaps in `chunking.py`.
- **AC-2 & ADV-002:** Enforced claim-level citation validation with verbatim quotes, `top_k=8`, `2.4%` CTR attribution guard, and negation/antonym polarity verification (`evidence.py`, `workflow.py`).
- **DQ-004 & ADV-004:** Implemented 48h freshness SLA logic (`freshness.py`, `workflow.py` Stage 2b) with explicit static benchmark exemption; formal written **PO approval pending**.
- **DQ-005 & ADV-003:** Implemented 3-tier influencer cap logic (`<= $10k` proceed including `$0` -> `REVIEW`, `$10k..$25k` `CONFLICT_DETECTED`, `> $25k` hard violation `REJECT`) + `_format_usd()` sub-cent precision; formal written **PO approval pending**.
- **ADV-001 & ADV-005:** Enforced `math.isfinite()` budget validation and `request_id` traversal allowlist (`workflow.py`).

## 2. Verification Evidence & Honest Limitations
- **Executed Tests (`Python 3.13.6`, `scikit-learn 1.9.1`):** `50/50` targeted tests passed (`0.66s`); `181/181` non-API tests passed (`4.41s`).
- **Blocked Tests:** `14` API endpoint tests (`tests/functional/test_api_endpoints.py`) remain **BLOCKED** in Windows sandbox (`socketpair` restriction); must be run by **Rhugved** in unsandboxed CI before merge.
- **Limitations:** `CitationValidator._has_polarity_mismatch()` uses deterministic lexical/regex rules (not deep NLI); `RAGPipeline.build_index()` must be run explicitly on merge because `is_index_stale()` checks raw document hashes only.
- **Independent Review:** **Parikshak** independent review is **PENDING**.

## 3. Rollback Considerations
- All changes are isolated in `hariom/cmo-v2-remediation` as a single reversible patch against `916022d6`. `data/marketing_corpus/` is untouched. Any integration can be cleanly reverted via `git revert` without database/ledger side effects.
