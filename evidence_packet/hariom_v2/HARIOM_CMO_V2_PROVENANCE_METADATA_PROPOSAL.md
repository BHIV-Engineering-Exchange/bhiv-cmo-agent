# Hariom Upadhyay — Provenance & Rights Metadata Report (DQ-003)

- **DQ-003 CMO Domain:** **RATIFIED** (Contract: `cmo.market_intelligence.v2`, Dataset: `ds-cmo-marketing-001`, Endorsed by: `Pratik Bhuwad — CMO Product Owner & Acting Workstream Lead`)
- **DQ-003 MDU Enterprise Registration:** **PENDING** (MDU retains global enterprise schema authority; no global schemas published or modified)

## Artifacts
- Schema: `docs/proposals/cmo_provenance_metadata.schema.json`
- Example Manifest: `docs/proposals/marketing_manifest_provenance_example.json`

## Required Provenance Fields Covered
- `content_hash` (SHA-256 source fingerprint)
- `document_id` (Source document ID)
- `rights` & `access_classification` (`SYNTHETIC_PREPROD_ONLY`, `INTERNAL_NON_PRODUCTION`)
- `retrieval_timestamp` & `effective_timestamp` (Extraction/publication timestamps)
- `freshness` (`sla_hours: 48.0`, `sla_status: "RATIFIED"`, `freshness_state`)

## MDU Registration Handover Request
Submit `docs/proposals/cmo_provenance_metadata.schema.json` to **MDU Parakosha** for formal enterprise schema registration under `cmo.market_intelligence.v2` (`ds-cmo-marketing-001`). Do not treat CMO domain ratification as completed enterprise MDU registration.
