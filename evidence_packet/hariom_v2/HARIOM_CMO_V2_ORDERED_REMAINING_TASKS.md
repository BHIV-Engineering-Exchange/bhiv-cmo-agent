# Hariom Upadhyay — Ordered Remaining Tasks

1. **P0 — Independent Parikshak Review (`PENDING`):** Submit `evidence_packet/hariom_v2/HARIOM_CMO_V2_STAGING_EVIDENCE_PACKET.md` and the updated clean patch for independent Parikshak verification before any merge.
2. **P0 — Rhugved & Rupam Code Review:** Review `chunking.py` (DQ-002), `evidence.py` + `workflow.py` (AC-2, DQ-004, DQ-005), and `freshness.py`; run `tests/functional/test_api_endpoints.py` (14 tests) in an unsandboxed CI runner.
3. **P1 — MDU Parakosha Enterprise Schema Registration (`PENDING`):** Submit `docs/proposals/cmo_provenance_metadata.schema.json` (`cmo.market_intelligence.v2` / `ds-cmo-marketing-001`) to MDU schema authority for enterprise registration.
4. **P1 — Lockfile / Pickle ABI Alignment (DQ-006):** Ensure CI and staging run on `scikit-learn==1.9.1` per `requirements.lock` (or migrate `embedding_model.pkl` to JSON vocabulary) and rebuild `data/marketing_index/` upon merge.
5. **P2 — Deferred Production Gates (`BLOCKED / NOT AUTHORIZED`):** Repository pushes, canonical `main` merges, live MASTERDB integration (`BLK-001`/`BLK-002`), and any customer/personal data ingestion (requires GC SHAKTI compliance sign-off) remain deferred.
