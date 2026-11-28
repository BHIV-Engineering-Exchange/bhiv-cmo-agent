# Hariom Upadhyay — Stakeholder Action Messages (Post-PO Decisions)

## 1. To Rhugved (Core Runtime & API Owner)
- **Code Review:** Please review the updated patch (`chunking.py`, `evidence.py`, `freshness.py`, `workflow.py`, and regression tests including `test_dq005_influencer_boundaries.py`).
- **Blocked API Tests & DQ-006:** Please run `tests/functional/test_api_endpoints.py` (14 tests) in an unsandboxed CI runner and enforce `requirements.lock` (`scikit-learn==1.9.1`).

## 2. To Rupam Patne (RAG Handover Owner)
- **RAG & Conflict Review:** Please review DQ-002 chunking, AC-2 claim-level citation validation, and DQ-005 3-tier influencer conflict handling preserving both `DOC-MKT-002` and `DOC-MKT-004`.

## 3. To MDU Schema Authority (Parakosha) — Registration Request
- **DQ-003 Registration Request:** `cmo.market_intelligence.v2` provenance schema (`docs/proposals/cmo_provenance_metadata.schema.json`, dataset `ds-cmo-marketing-001`) has been **ratified as a CMO domain proposal** by `Pratik Bhuwad — CMO Product Owner & Acting Workstream Lead`. Please review for formal enterprise MDU Parakosha registration.

## 4. To Parikshak (Independent Reviewer)
- **Independent Review Request (`PENDING`):** Please review `evidence_packet/hariom_v2/HARIOM_CMO_V2_STAGING_EVIDENCE_PACKET.md` for local/staging verification sign-off.

## 5. To Pratik Bhuwad (CMO Product Owner)
- Formal PO decisions for DQ-003 (CMO domain), DQ-004 (48h SLA), DQ-005 (3-tier influencer conflict), and local/staging governance endorsement have been applied. Production integrations and PII remain `BLOCKED / NOT AUTHORIZED` pending Parikshak & GC SHAKTI.
