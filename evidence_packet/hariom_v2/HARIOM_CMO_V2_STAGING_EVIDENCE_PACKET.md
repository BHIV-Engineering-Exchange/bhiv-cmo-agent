# Hariom Upadhyay — Local Staging Evidence Packet (CMO V2)

**Branch:** `hariom/cmo-v2-remediation` (base `916022d62812358b3aef594e74e9cc2a61901fce`)
**Governance Authority:** **ENDORSED** by `Pratik Bhuwad — CMO Product Owner & Acting Workstream Lead` (Local Dev, Benchmark Evaluation, Staging Verification ONLY)
**Independent Parikshak Review:** **PENDING**
**Production Integration / Live Data / PII:** **BLOCKED / NOT AUTHORIZED**

## 1. PO Decisions Applied
- **DQ-004 (Freshness SLA):** `RATIFIED` (`cmo.market_intelligence.v2` / `ds-cmo-marketing-001`), 48h SLA + explicit static benchmark exemption (`freshness.py` + `workflow.py` Stage 2b).
- **DQ-005 (Influencer Budget Conflict):** `RATIFIED` — both `DOC-MKT-002` (`$25k`) and `DOC-MKT-004` (`$10k`) retained unmodified; 3-tier behavior (`<= $10k` proceed, `$10k..$25k` `CONFLICT_DETECTED`, `> $25k` hard violation `REJECT`).
- **DQ-003 (Provenance Schema):** `CMO DOMAIN: RATIFIED` (`cmo_provenance_metadata.schema.json`); `MDU ENTERPRISE REGISTRATION: PENDING`.

## 2. Verification Summary
- **Freshness Boundary Tests (`test_freshness_validation.py`):** `6/6` passed (including explicit vs inferred exemption).
- **Influencer Cap Boundary Tests (`test_dq005_influencer_boundaries.py`):** `3/3` passed (`$10,000`, `$10,000.01`, `$25,000`, `$25,000.01`).
- **AC-2 Semantic Grounding (`test_ac2_semantic_grounding.py`):** `5/5` passed.
- **DQ-002 Chunking (`test_chunking.py`):** `5/5` passed.
- **DEFECT-SEMANTIC-001 Linear TV Abstention:** `2/2` passed.
- **Non-API Suite:** `160/160` passed; `14` API endpoint tests (`test_api_endpoints.py`) **BLOCKED IN SANDBOX**.
