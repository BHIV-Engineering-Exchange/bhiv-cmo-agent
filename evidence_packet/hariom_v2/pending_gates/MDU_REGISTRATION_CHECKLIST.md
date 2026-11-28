# MDU Parakosha Schema Registration Checklist

- [x] Schema drafted (`docs/proposals/cmo_provenance_metadata.schema.json`, JSON Schema Draft 2020-12)
- [x] All 13 mandatory provenance/rights/freshness fields included
- [x] Example manifest validated (`jsonschema.validate()` passed for `DOC-MKT-001`..`004`)
- [x] SHA-256 `content_hash` verified against actual source files on disk
- [x] Zero unauthorized modification to canonical MDU global schemas
- [ ] **PENDING:** Written **PO approval pending** (no signed PO approval artifact exists on disk)
- [ ] **NOT REGISTERED (External — MDU Schema Authority):** Review and register schema in MDU Parakosha (`https://parakosha.blackholeinfiverse.com`)
- [ ] **NOT REGISTERED (External — MDU Schema Authority):** Issue canonical lineage IDs and confirm registration status (close `BLK-004`)
