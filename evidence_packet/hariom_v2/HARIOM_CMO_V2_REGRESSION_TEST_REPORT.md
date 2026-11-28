# Hariom Upadhyay — Regression Test & Inventory Reconciliation Report

## 1. Test Inventory Reconciliation (`136` vs `159` vs `174`)
- **`136` tests:** Historical Nov 18 baseline (`b7a795c` -> `db032d6`, 27 test files).
- **`159` tests (`HEAD 916022d6`):** `136` baseline + `14` (`tests/functional/test_api_endpoints.py`) + `5` (`tests/regression/test_ui_and_workflow_fixes.py`) + `4` (`tests/regression/test_qa_hardening_defects.py`).
- **`174` tests (current `hariom/cmo-v2-remediation`):** `159` base + `1` DQ-002 chunking + `6` DQ-004 freshness + `5` AC-2 semantic grounding + `3` DQ-005 influencer boundary tests = **`174` total tests** (`160` non-API + `14` API endpoint tests).

## 2. Exact Executed Test Results (`Python 3.13.6`, `scikit-learn 1.9.1`, `pytest 9.0.2`)
- **Non-API Suite (`python -m pytest --ignore=tests/functional/test_api_endpoints.py -q --tb=short`):** **160 passed, 0 failed** (covering DQ-002 `5/5`, DQ-004 `6/6`, AC-2 `5/5`, DQ-005 `3/3`, `DEFECT-SEMANTIC-001` `2/2`, and all 139 remaining unit/integration/functional/security/task3 tests).
- **API Endpoint Suite (`tests/functional/test_api_endpoints.py` — 14 tests):** **BLOCKED IN SANDBOX** (`TestClient.__enter__` -> `asyncio._make_self_pipe` `socket.accept()` hang); requires unsandboxed CI execution by Rhugved.
