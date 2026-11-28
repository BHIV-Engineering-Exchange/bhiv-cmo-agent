# Hariom Upadhyay — AC-2 Claim-to-Citation Audit (`REQ-MKT-2026-LI-01`)

## 1. Historical vs Remediated Comparison
- **Historical Snapshot (`evidence_packet/api_samples/req_mkt_2026_li_01_proposal_evaluated.json`):**
  - `verified_facts` contained truncated mid-word fragments (`"ed data grounding..."`, `"sequently, active planned..."`, `"Search, LinkedIn Ads..."`).
  - `Citation.quote` was `null`, `is_valid=True` was hardcoded in `workflow.py:326`, `DOC-MKT-001-C003` (25% SQLs) was missing, and `DOC-MKT-003-C004` (CTR/CAC/ROAS) was omitted from `citations` due to `seen_docs` deduplication.
  - **Historical AC-2 Verdict:** `PARTIAL / FAIL (Structurally Valid, Semantically Defective)`.
- **Remediated Isolated Copy (`hariom/cmo-v2-remediation`):**
  - `DecisionWorkflow.evaluate_proposal` retrieves `top_k=8`, extracts complete sentences with verbatim `Citation.quote`, and validates every claim through `CitationValidator.validate_claim_citation(..., require_quote=True)`.
  - Note on chunk IDs after DQ-002 fix (22 -> 20 chunks): `DOC-MKT-003-C003` now holds historical metrics (previously `C004`), and `DOC-MKT-003-C005` holds unverified media gaps (previously `C006`).

## 2. Remediated Claim-to-Citation Table (`REQ-MKT-2026-LI-01-CHECK`)

| Required Source | Claim Extracted | Document / Chunk ID | Quote Validated? | Semantic Verdict |
|---|---|---|---|---|
| `DOC-MKT-001-C003` | The primary objective for Q4 is driving a 25% increase in sales-qualified enterprise leads (SQLs). | `DOC-MKT-001` / `DOC-MKT-001-C003` | Yes (verbatim) | **PASS** |
| `DOC-MKT-001-C004` | Paid Social: LinkedIn Sponsored Content targeting Engineering Managers, VP of Engineering, and Chief Technology Officers. | `DOC-MKT-001` / `DOC-MKT-001-C004` | Yes (verbatim) | **PASS** |
| `DOC-MKT-002-C005` | Paid Social (LinkedIn Ads): Capped at a maximum allocation of $15,000. | `DOC-MKT-002` / `DOC-MKT-002-C005` | Yes (verbatim) | **PASS** |
| `DOC-MKT-003-C003` (was `C004`) | Customer Acquisition Cost (CAC): Historical average CAC is $32.00 per qualified lead... (plus 2.4% combined CTR in assumptions) | `DOC-MKT-003` / `DOC-MKT-003-C003` | Yes (verbatim) | **PASS** |
| `DOC-MKT-003-C004` / `C005` (was `C006`) | Historical performance data is strictly limited to Google Search, LinkedIn Ads, and technical whitepaper syndication. | `DOC-MKT-003` / `DOC-MKT-003-C004` | Yes (verbatim) | **PASS** |
| `DOC-MKT-004` | Influencer and KOL Partnerships cap ($10,000) / compliance context | `DOC-MKT-004` / `DOC-MKT-004-C004` | Yes (verbatim) | **PASS** |

- **2.4% CTR Guard:** Explicitly enforced in `CitationValidator.validate_claim_citation()` (rejects any claim calling 2.4% CTR `"LinkedIn-only"` or `"LinkedIn-specific"`) and `workflow.py` assumptions (`"combined paid search and social benchmarks (CTR ~2.4%, CAC ~$32.00)"`).
- **Remediated AC-2 Verdict (Isolated Copy):** **VERIFIED PASS** (`tests/regression/test_ac2_semantic_grounding.py`: 5/5 passed).
