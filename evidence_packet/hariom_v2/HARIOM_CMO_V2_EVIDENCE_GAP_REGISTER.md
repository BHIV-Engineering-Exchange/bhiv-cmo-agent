# Hariom Upadhyay — Evidence Gap Register

| Gap ID | Item | Current Status | Owner | Unblock Condition |
|---|---|---|---|---|
| **GAP-H01** | 7 original unpushed Hariom files (`CMO_V2_DATA_CORPUS_EVALUATION_HARIOM.md`, 3 scripts, 3 JSONs) | **NOT REPRODUCIBLE** | Hariom | Replaced by `scripts/evaluate_cmo_marketing_reproducible.py` |
| **GAP-H02** | DQ-004 48h freshness SLA ratification | **CLOSED (RATIFIED)** | Pratik Bhuwad (PO) | Ratified for `cmo.market_intelligence.v2` / `ds-cmo-marketing-001` (local/staging only) |
| **GAP-H03** | Governance sign-off | **CLOSED (ENDORSED)** | Pratik Bhuwad (PO) | Endorsed for local dev, benchmark eval, and staging verification |
| **GAP-H04** | DQ-003 MDU enterprise schema registration | **PENDING** | MDU Schema Authority | MDU Parakosha registration of `cmo_provenance_metadata.schema.json` |
| **GAP-H05** | `tests/functional/test_api_endpoints.py` (14 tests) | **BLOCKED IN SANDBOX** | Rhugved | Unsandboxed CI execution (`TestClient` socketpair restriction) |
| **GAP-H06** | Independent Parikshak review | **PENDING** | Parikshak | Independent audit of staging evidence packet |
| **GAP-H07** | Production integration, live data & PII | **BLOCKED / NOT AUTHORIZED** | GC SHAKTI / Kavy / PO | Parikshak review + GC SHAKTI compliance + MASTERDB prod blockers |
