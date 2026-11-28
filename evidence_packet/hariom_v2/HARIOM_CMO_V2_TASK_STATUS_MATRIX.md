# Hariom Upadhyay — CMO V2 Task Status Matrix

| Deliverable / Item | Policy / Authority Status | Implementation / Verification Status | Evidence | Remaining Dependency |
|---|---|---|---|---|
| **DQ-004: 48h Freshness SLA (`cmo.market_intelligence.v2` / `ds-cmo-marketing-001`)** | **RATIFIED** | **VERIFIED (Local/Staging)** | `src/evidence_rag/freshness.py`, `workflow.py`, `tests/unit/test_freshness_validation.py` (`6/6` pass) | Independent Parikshak review; production/live integrations remain **BLOCKED / NOT AUTHORIZED** |
| **DQ-005: Influencer Budget Conflict ($25k vs $10k)** | **RATIFIED** | **VERIFIED (Local/Staging)** | `src/evidence_rag/workflow.py`, `tests/regression/test_dq005_influencer_boundaries.py` (`3/3` pass: `$10k`, `$10,000.01`, `$25k`, `$25,000.01`) | Independent Parikshak review |
| **DQ-003: Provenance Metadata (`cmo.market_intelligence.v2`)** | **CMO DOMAIN: RATIFIED** | **MDU REGISTRATION: PENDING** | `docs/proposals/cmo_provenance_metadata.schema.json`, `marketing_manifest_provenance_example.json` | MDU Parakosha enterprise schema registration |
| **Governance Sign-Off** | **ENDORSED** *(Pratik Bhuwad — CMO Product Owner & Acting Workstream Lead)* | **Local Dev / Benchmark / Staging Only** | PO Decision Record (`2026-11-26`); PII/live customer data prohibited without GC SHAKTI | Independent Parikshak review (**PENDING**) |
| **DQ-002: Duplicate Heading & Boundary Chunking** | Approved in Remediation | **VERIFIED COMPLETE (Local/Staging)** | `src/evidence_rag/chunking.py`, `tests/unit/test_chunking.py` (`5/5` pass), `22` -> `20` chunks | Rhugved / Rupam code review |
| **AC-2: Claim-Level Semantic Grounding** | Required by V2 | **VERIFIED COMPLETE (Local/Staging)** | `src/evidence_rag/evidence.py`, `workflow.py`, `tests/regression/test_ac2_semantic_grounding.py` (`5/5` pass) | Rhugved / Rupam code review |
| **`DEFECT-SEMANTIC-001` (Linear TV Abstention)** | Required by V2 | **VERIFIED PASS** | `test_linear_tv_query_abstains_canonical_refusal` & `test_workflow_linear_tv_abstains_insufficient_evidence` (`2/2` pass) | None |
| **Original 7 Unpushed 14-Query Files** | — | **NOT REPRODUCIBLE** | Absent from `bhiv-cmo-agent` and local workspace | Replacement benchmark verified (`100%` Recall@4) |
| **14 API Endpoint Tests (`test_api_endpoints.py`)** | — | **BLOCKED IN SANDBOX** | `faulthandler` confirmed `TestClient` `_make_self_pipe` `socket.accept()` hang | Rhugved unsandboxed CI run |
| **Independent Parikshak Review** | Required | **PENDING** | `HARIOM_CMO_V2_STAGING_EVIDENCE_PACKET.md` | Parikshak execution |
| **Production Integration / Live Data / Repo Push** | **BLOCKED / NOT AUTHORIZED** | **BLOCKED / NOT AUTHORIZED** | Deferred per PO governance restriction | Parikshak review, GC SHAKTI, MDU, MASTERDB prod |
