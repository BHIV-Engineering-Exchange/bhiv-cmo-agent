# BHIV CMO Agent V2 — Post-Exam Verification Report

**Owner:** Hariom Upadhyay  
**Work Resumed Date:** `2026-11-26T14:04:03+05:30`  
**Repository:** `C:\Users\Microsoft\.gemini\antigravity\scratch\bhiv-cmo-agent-hariom-remediation`  
**Branch / Base Commit:** `hariom/cmo-v2-remediation` @ `916022d62812358b3aef594e74e9cc2a61901fce`

---

## 1. Task 1 — API Test Execution Blocker (`tests/functional/test_api_endpoints.py`, 14 Tests)
- **Installed Stack (`Python 3.13.6`):** `fastapi==0.118.0`, `starlette==0.48.0`, `httpx==0.27.0`, `anyio==4.11.0`.
- **Alternative Environment Probes:**
  - `wsl --status`: `Wsl/E_ACCESSDENIED` (blocked in sandbox).
  - `docker info`: `C:\Users\Microsoft\.docker\config.json: Access is denied` (daemon unreachable in sandbox).
  - `TestClient` (`ProactorEventLoop`) & `httpx.ASGITransport` with `WindowsSelectorEventLoopPolicy` (`asyncio.run()`): both hang at `socket.py:295 accept()` -> `_fallback_socketpair` -> `_make_self_pipe` during `asyncio.Runner.__enter__`.
- **Conclusion:** Root cause is a **Windows sandbox networking restriction on `socketpair()` loopback `accept()`**, not a FastAPI route or fixture deadlock. All 14 API tests remain classified as **`BLOCKED` in sandbox**.
- **Exact CI Command for Unsandboxed Runner:**
  ```powershell
  python -m pytest tests/functional/test_api_endpoints.py -v --tb=short
  ```

---

## 2. Task 2 — Full Regression Verification & Benchmark
- **Exact Test Command (`Python 3.13.6`, `scikit-learn 1.9.1`, `pytest 9.0.2`):**
  ```powershell
  python -m pytest --ignore=tests/functional/test_api_endpoints.py -v --tb=short
  ```
- **Result:** **161 passed in 3.82s** (`160` prior non-API tests + `1` new DQ-005 sub-cent precision regression test).
- **Raw Log:** `evidence_packet/hariom_v2/post_exam_pytest_161.log` (timestamped `2026-11-26T14:06:xx+05:30`).
- **Verified Scopes:**
  - AC-2 semantic grounding (`5/5`), DQ-002 chunking (`5/5`), DQ-004 freshness (`6/6`), DQ-005 influencer boundaries (`4/4`), `DEFECT-SEMANTIC-001` Linear TV abstention (`2/2`), DQ-003 provenance proposal, and 14-query reproducible benchmark (`Recall@4: 1.0`, `Precision@4: 0.5455`, `MRR: 0.9394`, `Status Accuracy: 1.0`, `Domain Isolation: 1.0`, `Citation Validity: 1.0`).

---

## 3. Task 3 — DQ-005 Cosmetic Precision Fix (`$25,000.001`)
- **Defect Confirmed:** `src/evidence_rag/workflow.py` previously formatted `req_budget` with `${req_budget:,.2f}` (lines `299`, `304`, `534`, `539`), displaying `25000.001` as `$25,000.00` in logs, `inferences`, and `risk_assessment` while float comparisons (`req_budget > 25000.0`) already triggered `REJECT` accurately.
- **Fix Applied:** Added `DecisionWorkflow._format_usd(amount: float)` in `src/evidence_rag/workflow.py` (uses `f"${amount:,.2f}"` for exact cent values and `f"${amount:,.6f}".rstrip("0").rstrip(".")` when sub-cent precision is present).
- **Regression Test Added:** `test_dq005_subcent_precision_preserved_in_outputs` in `tests/regression/test_dq005_influencer_boundaries.py` (verifies `$25,000.001` is preserved in `risk_assessment` and `inferences`).

---

## 4. Task 4 — Patch, Corpus & Package Verification
- **Preserved Desktop Patch V2:** `C:\Users\Microsoft\Desktop\hariom-cmo-v2-remediation-review-v2.patch` (`107,216` bytes, SHA256: `C6148F2A1BBFC17C05477ED2801C53F4F5150D431973039CB2BBBEDBEBC8595F`) — `git apply --check` passed (`0`). *(Note: the DQ-005 `_format_usd` fix and `post_exam_pytest_161.log` were added locally on `hariom/cmo-v2-remediation` after `v2.patch` was frozen, keeping `v2.patch` and all prior handover ZIPs intact.)*
- **Preserved ZIPs:**
  - `HARIOM_CMO_V2_REVIEWER_HANDOVER_V2.zip` (`39,449` bytes, SHA256: `9427124E2485399C96A1855DB4E8EC95881ABE99D2A7CA5960BD167CB83732B9`)
  - `HARIOM_CMO_V2_FINAL_SELF_AUDIT_EVIDENCE.zip` (`13,389` bytes, SHA256: `203D15F67031F45E096C1D7E4E4BACF4060032756D9B18C6E771D66AC7D96BD1`)
- **Corpus & Safety:** `git diff -- data/marketing_corpus/` is empty; `0` secrets or PII; no commit, push, merge, PR, or production action occurred.
