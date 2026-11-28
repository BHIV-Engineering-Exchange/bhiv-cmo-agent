# MDU Parakosha Enterprise Schema Registration Request (DQ-003 / BLK-004)

- **MDU Schema Registration:** **NOT REGISTERED** *(Portal/API access unavailable in offline sandbox; MDU Schema Authority action required)*
- **PO Approval Status:** **PO approval pending** *(No written/signed PO approval evidence exists on disk in the repository)*
- **Governance Approval:** **NOT RECEIVED**
- **Integration Status:** **NOT AUTHORIZED**
- **Target Authority:** **MDU Parakosha** (Canonical Schema & Data Provenance/Lineage Authority — `https://parakosha.blackholeinfiverse.com`)
- **Contract / Dataset:** `cmo.market_intelligence.v2` | `ds-cmo-marketing-001`
- **Submitted By:** `Hariom Upadhyay` (Data Quality, Corpus Integrity & Evaluation Lead)
- **Date:** `2026-11-26T15:58:00+05:30`

## 1. Schema Artifact Submitted
- **Schema File:** `docs/proposals/cmo_provenance_metadata.schema.json` (`$id: https://bhiv.internal/schemas/proposals/cmo_provenance_metadata.schema.json`, JSON Schema Draft 2020-12)
- **Validated Example Manifest:** `docs/proposals/marketing_manifest_provenance_example.json` *(Note: `endorsed_by` / `proposal_status` fields in the example fixture are proposed placeholders; formal written **PO approval pending**)*
- **Validation Evidence:** `jsonschema.validate()` passed against all 4 documents (`DOC-MKT-001`..`004`), with SHA-256 `content_hash` verified against disk bytes (`mdu_schema_validation.log`).

## 2. Mandatory Provenance Fields (13 Required)
`document_id`, `owner`, `rights`, `access_classification`, `approved_purpose`, `provenance_ref`, `source_type`, `version`, `retrieval_timestamp`, `effective_timestamp`, `freshness` (`sla_hours`, `sla_status`, `freshness_state`), `quality_status`, `content_hash` (64-char SHA-256 hex).

## 3. Compatibility & Non-Invasiveness
- Global MDU schemas and `src/evidence_rag/schemas.py` (`DocumentMetadata`) were **not** modified.
- All 4 `DOC-MKT-*` records are classified `SYNTHETIC_PREPROD_ONLY` / `INTERNAL_NON_PRODUCTION` (zero PII/customer data).

## 4. Remaining External Actions
1. **Pratik Bhuwad / Prateek (PO):** Written **PO approval pending**.
2. **MDU Parakosha Schema Authority:** Review `cmo_provenance_metadata.schema.json`, assign canonical lineage IDs, and perform formal registration (`NOT REGISTERED` until official ID is returned).
