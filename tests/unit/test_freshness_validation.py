"""Unit tests for proposed 48-hour freshness and provenance timestamp validation (DQ-004)."""
from datetime import datetime, timezone, timedelta
from evidence_rag.freshness import FreshnessValidator, FreshnessStatus


def test_fresh_document_within_48_hours():
    ref = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
    ts = (ref - timedelta(hours=12)).isoformat()
    validator = FreshnessValidator()
    res = validator.evaluate_timestamp("DOC-MKT-001", ts, reference_time=ref)

    assert res.status == FreshnessStatus.FRESH
    assert res.is_fresh is True
    assert res.requires_human_review is False
    assert res.policy_status == "RATIFIED"
    assert res.contract_id == "cmo.market_intelligence.v2"
    assert res.dataset_id == "ds-cmo-marketing-001"
    assert res.age_hours == 12.0


def test_stale_document_older_than_48_hours():
    ref = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
    validator = FreshnessValidator(max_age_hours=48.0, policy_status="PROPOSED")
    res = validator.evaluate_timestamp("DOC-MKT-001", "2026-09-15T10:00:00Z", reference_time=ref)

    assert res.status == FreshnessStatus.STALE
    assert res.is_fresh is False
    assert res.age_hours > 48.0


def test_missing_and_invalid_timestamps_never_treated_as_fresh():
    ref = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
    validator = FreshnessValidator()

    res_missing = validator.evaluate_timestamp("DOC-MKT-002", None, reference_time=ref)
    assert res_missing.status == FreshnessStatus.MISSING_TIMESTAMP
    assert res_missing.is_fresh is False

    res_invalid = validator.evaluate_timestamp("DOC-MKT-002", "not-a-date", reference_time=ref)
    assert res_invalid.status == FreshnessStatus.INVALID_TIMESTAMP
    assert res_invalid.is_fresh is False

    # Naive timestamp without timezone must be rejected
    res_naive = validator.evaluate_timestamp("DOC-MKT-002", "2026-11-26T10:00:00", reference_time=ref)
    assert res_naive.status == FreshnessStatus.INVALID_TIMESTAMP
    assert res_naive.is_fresh is False


def test_timezone_offset_and_future_timestamp_handling():
    ref = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
    validator = FreshnessValidator()

    # +05:30 offset converted to UTC (16:30+05:30 == 11:00 UTC -> 1h old)
    res_tz = validator.evaluate_timestamp("DOC-MKT-003", "2026-11-26T16:30:00+05:30", reference_time=ref)
    assert res_tz.status == FreshnessStatus.FRESH
    assert res_tz.is_fresh is True
    assert res_tz.age_hours == 1.0

    res_future = validator.evaluate_timestamp("DOC-MKT-004", "2026-11-27T12:00:00Z", reference_time=ref)
    assert res_future.status == FreshnessStatus.FUTURE_DATED
    assert res_future.is_fresh is False


def test_manifest_freshness_audit_flags_stale_corpus():
    ref = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
    validator = FreshnessValidator()
    manifest = {
        "documents": [
            {"document_id": "DOC-MKT-001", "updated_at": "2026-09-15T10:00:00Z"},
            {"document_id": "DOC-MKT-002", "updated_at": "2026-11-26T10:00:00Z"},
        ]
    }
    report = validator.evaluate_manifest(manifest, reference_time=ref)
    assert report["policy_status"] == "RATIFIED"
    assert report["all_fresh"] is False
    assert report["requires_human_review"] is True
    assert report["non_fresh_document_ids"] == ["DOC-MKT-001"]


def test_explicit_static_benchmark_exemption_and_no_inference():
    """Static benchmark exemptions must be explicit with a reason, never inferred."""
    ref = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
    validator = FreshnessValidator()

    # Flag True WITHOUT reason -> must NOT be exempted
    res_no_reason = validator.evaluate_timestamp(
        "DOC-MKT-001",
        "2026-09-15T10:00:00Z",
        reference_time=ref,
        static_benchmark_exempt=True,
        exemption_reason="",
    )
    assert res_no_reason.status == FreshnessStatus.STALE
    assert res_no_reason.is_fresh is False
    assert res_no_reason.requires_human_review is True

    # Flag True WITH explicit documented reason -> exempted
    res_exempt = validator.evaluate_timestamp(
        "DOC-MKT-001",
        "2026-09-15T10:00:00Z",
        reference_time=ref,
        static_benchmark_exempt=True,
        exemption_reason="Approved synthetic benchmark ds-cmo-marketing-001",
    )
    assert res_exempt.status == FreshnessStatus.EXEMPT_STATIC_BENCHMARK
    assert res_exempt.is_fresh is True
    assert res_exempt.static_benchmark_exempt is True
    assert res_exempt.requires_human_review is False
