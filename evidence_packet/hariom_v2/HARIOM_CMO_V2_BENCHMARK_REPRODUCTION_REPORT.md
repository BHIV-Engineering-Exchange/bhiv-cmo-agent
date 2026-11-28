# Hariom Upadhyay — Benchmark Reproduction Report (Phase 5)

## 1. Recovery Audit of Original 7 Unpushed Files
Searched `bhiv-cmo-agent` (`main` @ `916022d6`) and all `*bhiv*` workspace directories for:
`CMO_V2_DATA_CORPUS_EVALUATION_HARIOM.md`, `scripts/audit_citations.py`, `scripts/evaluate_cmo_marketing.py`, `scripts/evaluate_data_quality.py`, `evaluation/results/citation_audit_samples.json`, `evaluation/results/cmo_marketing_benchmark_results.json`, `evaluation/results/cmo_data_quality_results.json`.
- **Result:** **NOT FOUND (`NOT REPRODUCIBLE`).**
- **Historical Unverified Claims Preserved:** `Recall@4: 95.83%`, `Precision@4: 31.25%`, `MRR: 0.9583`, `Status accuracy: 78.57%`, `Domain isolation: 100%`.

## 2. Reproducible Replacement Benchmarks (Verified `2026-11-26`)
1. **14-Query Marketing Replacement (`scripts/evaluate_cmo_marketing_reproducible.py` -> `evaluation/results/cmo_marketing_reproducible_benchmark.json`):**
   - Corpus/Index: `data/marketing_corpus` (4 docs, fingerprint `df043f7b04f03920`, remediated `20`-chunk index) + `data/index` (`348` chunks for domain isolation).
   - **Mean Recall@4:** `100.0%` (`1.0`, 11 applicable queries)
   - **Mean Precision@4:** `54.55%` (`0.5455`)
   - **MRR:** `0.9394`
   - **Status Accuracy:** `100.0%` (`14/14`)
   - **Domain Isolation:** `100.0%` (`1.0`, 0 marketing chunks leaked into Python query)
   - **Citation Validity Rate:** `100.0%` (`1.0`)
2. **25-Query Canonical Benchmark (`evaluation/questions.jsonl`):**
   - **Status Accuracy:** `100.0%` (`25/25`), **Retrieval Success:** `94.74%` (`18/19`), **Failure Detection:** `100.0%` (`8/8`), **Citation Validity:** `100.0%` (`44/44`), **Avg Latency:** `11.33 ms`.
