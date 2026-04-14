from datetime import datetime, timedelta

from app.crawlers import run_ingest
from app.schemas import Document


def _build_document(
    *,
    doc_id: str,
    source_url: str,
    title: str,
    content: str,
    collected_at: datetime,
) -> Document:
    return Document(
        doc_id=doc_id,
        source_type="html",
        source_url=source_url,
        title=title,
        content=content,
        category="academic",
        department="academic_affairs",
        published_at=None,
        collected_at=collected_at,
    )


def test_run_ingest_executes_end_to_end_pipeline(monkeypatch, capsys) -> None:
    now = datetime(2026, 4, 10, 12, 0, 0)
    duplicate_content = "duplicate-notice-" * 80
    long_content = "long-notice-" * 120

    source_config = [
        {
            "name": "academic_notices",
            "seed_urls": ["https://example.com/notices"],
            "category": "academic",
            "department": "academic_affairs",
            "max_pages": 5,
            "max_depth": 1,
            "embed": True,
            "embedding_limit": 2,
        }
    ]

    documents = [
        _build_document(
            doc_id="dup-old",
            source_url="https://example.com/notices/1",
            title="Academic Notice",
            content=duplicate_content,
            collected_at=now,
        ),
        _build_document(
            doc_id="dup-new",
            source_url="https://example.com/notices/2",
            title="Academic Notice",
            content=duplicate_content,
            collected_at=now + timedelta(minutes=1),
        ),
        _build_document(
            doc_id="unique",
            source_url="https://example.com/notices/3",
            title="Second Notice",
            content=long_content,
            collected_at=now,
        ),
    ]

    monkeypatch.setattr(run_ingest, "load_sources_config", lambda _: source_config)
    monkeypatch.setattr(
        run_ingest,
        "collect_documents_with_crawl4ai",
        lambda _: documents,
    )
    monkeypatch.setattr(run_ingest, "embed_chunks", lambda chunks: [object() for _ in chunks])

    run_ingest.main()

    captured = capsys.readouterr()
    assert "[academic_notices] raw_documents=3 documents=2" in captured.out
    assert "exact_duplicates_removed=1" in captured.out
    assert "version_duplicates_removed=0" in captured.out
    assert "chunks=4 embedded_chunks=2" in captured.out
    assert "total_documents=2" in captured.out
    assert "total_chunks=4" in captured.out
    assert "total_embedded_chunks=2" in captured.out
