# External Dependency & Owner Matrix

| Dependency / Gate | Current Status | Responsible Owner | Required Action |
|---|---|---|---|
| **PO Approval (DQ-003, DQ-004, DQ-005, Integration)** | **PO approval pending / NOT RECEIVED** | **Pratik Bhuwad / Prateek (PO)** | Provide written PO approval & sign `PO_APPROVAL_CHECKLIST_AND_DECISION_RECORD.md` for staging/CI integration only |
| **Independent Review** | **PENDING** | **Parikshak** | Audit `HARIOM_CMO_V2_FINAL_HANDOVER.zip` / V4 patch and issue review verdict |
| **14 API Endpoint Tests** | **BLOCKED (Sandbox)** | **Rhugved** | Run `python -m pytest tests/functional/test_api_endpoints.py -v --tb=short` in unsandboxed CI & rebuild index on merge |
| **MDU Schema Registration (`BLK-004`)** | **NOT REGISTERED** | **MDU Parakosha Schema Authority** | Register `cmo_provenance_metadata.schema.json` (`cmo.market_intelligence.v2` / `ds-cmo-marketing-001`) and issue lineage IDs |
| **Integration / Merge / Deployment** | **NOT AUTHORIZED** | **PO & Governance** | Remains unauthorized until all external gates above clear |
| **Production MASTERDB / PII** | **NOT AUTHORIZED / BLOCKED** | **Kavy / TANTRA / GC SHAKTI** | Resolve `BLK-001` (RS256 token), `BLK-002` (`MASTERDB_DATABASE_URL`), and GC SHAKTI compliance |
