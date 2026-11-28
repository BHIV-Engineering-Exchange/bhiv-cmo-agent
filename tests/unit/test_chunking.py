"""Unit tests for boundary-aware chunking and chunk identity specification."""
import pytest
from evidence_rag.chunking import Chunker
from evidence_rag.config import ChunkingConfig
from evidence_rag.schemas import Document, DocumentMetadata


def test_chunking_creates_deterministic_ids(sample_document):
    chunker = Chunker(ChunkingConfig(chunk_size_chars=200, chunk_overlap_chars=40))
    chunks = chunker.chunk_document(sample_document)

    assert len(chunks) >= 1
    for idx, c in enumerate(chunks, start=1):
        expected_id = f"DOC-999-C{idx:03d}"
        assert c.chunk_id == expected_id
        assert c.document_id == "DOC-999"
        assert c.chunk_index == idx - 1
        assert len(c.text) > 0


def test_chunking_preserves_sentence_boundaries():
    content = (
        "First complete sentence here. "
        "Second complete sentence here. "
        "Third complete sentence here. "
        "Fourth complete sentence here."
    )
    doc = Document(
        metadata=DocumentMetadata(
            document_id="DOC-888",
            title="Boundary Test",
            source="docs/boundary.md",
            source_type="technical_specification",
            version="1.0.0",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
            topic="Boundary"
        ),
        content=content,
        content_hash="boundary_hash"
    )
    chunker = Chunker(ChunkingConfig(chunk_size_chars=80, chunk_overlap_chars=20))
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    # Check that chunks do not cut off words abruptly
    for c in chunks:
        assert not c.text.startswith(" ")
        assert not c.text.endswith(" ")


def test_chunking_merges_tiny_orphan_fragments():
    content = "A substantial opening paragraph describing the core system.\n\nTiny."
    doc = Document(
        metadata=DocumentMetadata(
            document_id="DOC-777",
            title="Orphan Test",
            source="docs/orphan.md",
            source_type="technical_specification",
            version="1.0.0",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
            topic="Orphan"
        ),
        content=content,
        content_hash="orphan_hash"
    )
    chunker = Chunker(ChunkingConfig(chunk_size_chars=200, min_chunk_chars=40))
    chunks = chunker.chunk_document(doc)

    # The 5-char 'Tiny.' should be merged into the previous chunk instead of being an orphan
    assert len(chunks) == 1
    assert "Tiny." in chunks[0].text


def test_chunking_empty_document():
    doc = Document(
        metadata=DocumentMetadata(
            document_id="DOC-000",
            title="Empty",
            source="docs/empty.md",
            source_type="technical_specification",
            version="1.0.0",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
            topic="Empty"
        ),
        content="",
        content_hash="empty_hash"
    )
    chunker = Chunker()
    assert chunker.chunk_document(doc) == []


def test_chunking_no_duplicate_heading_only_chunks_and_no_midword_overlap():
    """DQ-002 regression: headings must not form duplicate standalone chunks and overlap must align to word boundaries."""
    content = (
        "# Historical Campaign Performance and ROI Benchmarks\n\n"
        "## Metadata\n"
        "- **document_id:** DOC-MKT-003\n"
        "- **title:** Historical Campaign Performance and ROI Benchmarks\n"
        "- **source:** data/marketing_corpus/DOC-MKT-003_past_performance_benchmarks.md\n"
        "- **source_type:** analytics_benchmark\n"
        "- **version:** 1.0.0\n"
        "- **created_at:** 2026-09-02T10:00:00Z\n"
        "- **updated_at:** 2026-09-17T14:00:00Z\n"
        "- **topic:** Performance Benchmarks\n\n"
        "## 1. Past Campaign Metrics\n"
        "Across preceding quarters, enterprise acquisition campaigns yielded verified baseline metrics "
        "including a 2.4% combined CTR and $32.00 historical average CAC."
    )
    doc = Document(
        metadata=DocumentMetadata(
            document_id="DOC-MKT-003",
            title="Historical Campaign Performance and ROI Benchmarks",
            source="data/marketing_corpus/DOC-MKT-003_past_performance_benchmarks.md",
            source_type="analytics_benchmark",
            version="1.0.0",
            created_at="2026-09-02T10:00:00Z",
            updated_at="2026-09-17T14:00:00Z",
            topic="Performance Benchmarks"
        ),
        content=content,
        content_hash="dq002_hash"
    )
    chunker = Chunker(ChunkingConfig(chunk_size_chars=400, chunk_overlap_chars=60, min_chunk_chars=40))
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    # C001 must not be a heading-only chunk duplicated inside C002
    assert "\n" in chunks[0].text
    assert chunks[0].text != chunks[1].text[:len(chunks[0].text)]
    # No chunk should start with a partial lowercase word fragment
    for c in chunks:
        first_token = c.text.lstrip().split()[0]
        assert first_token[0].isupper() or first_token[0] in "#-*0123456789$"
