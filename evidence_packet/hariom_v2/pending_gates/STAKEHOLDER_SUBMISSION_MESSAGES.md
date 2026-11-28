# Copy-Paste Stakeholder Submission Messages (Not Sent)

## 1. Message to MDU Parakosha Registration Owner
```text
Hi MDU Parakosha Schema Authority Team,

I am submitting the CMO V2 provenance metadata schema proposal (`cmo.market_intelligence.v2` / dataset `ds-cmo-marketing-001`) for formal enterprise schema registration (tracking blocker BLK-004).

Current status:
- MDU Schema Registration: NOT REGISTERED
- PO Approval: PO approval pending (no written PO sign-off on file yet)
- Integration: NOT AUTHORIZED

Artifacts included in `HARIOM_CMO_V2_PENDING_GATES_SUBMISSION.zip` (`01_mdu_registration/`):
- Schema: `cmo_provenance_metadata.schema.json` (JSON Schema Draft 2020-12, 13 required fields including SHA-256 `content_hash`, `document_id`, `rights`, `access_classification`, `retrieval_timestamp`, `effective_timestamp`, and `freshness`).
- Validated Example Manifest: `marketing_manifest_provenance_example.json` (`jsonschema.validate()` passed for DOC-MKT-001..004; all SHA-256 hashes verified).
- Registration Request & Checklist: `MDU_PARAKOSHA_SCHEMA_REGISTRATION_REQUEST.md`, `MDU_REGISTRATION_CHECKLIST.md`.

Global MDU schemas have NOT been modified. Please review, register in MDU Parakosha once PO approval is confirmed, and share the official registration/lineage IDs.

Thanks,
Hariom Upadhyay
```

## 2. Message to Pratik (CMO Product Owner — Formal Governance Approval Request)
```text
Hi Pratik,

All local remediation work for BHIV CMO Agent V2 (V4) is complete and verified (`50/50` targeted tests, `181/181` non-API tests, `git diff --check` and clean-base `git apply --check` passed, `data/marketing_corpus/` unchanged).

I am submitting `HARIOM_CMO_V2_PENDING_GATES_SUBMISSION.zip` containing the formal Governance Approval Request (`PO_GOVERNANCE_APPROVAL_REQUEST.md`) and Decision Record Template (`PO_APPROVAL_CHECKLIST_AND_DECISION_RECORD.md`) for the **NEXT integration step (staging/CI integration) ONLY** — NOT production deployment.

Current external gate statuses:
1. PO Approval (DQ-003, DQ-004, DQ-005, Integration): PO approval pending (Governance approval NOT RECEIVED).
2. Independent Parikshak review: PENDING.
3. Unsandboxed CI execution of 14 sandbox-blocked API tests by Rhugved: BLOCKED / EXTERNAL.
4. MDU Parakosha enterprise provenance schema registration (`cmo_provenance_metadata.schema.json`): NOT REGISTERED.
5. Integration: NOT AUTHORIZED.

No commit, push, merge, or deployment has been performed. Please provide your written PO decision in the decision record.

Thanks,
Hariom Upadhyay
```
