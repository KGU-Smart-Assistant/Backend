import json
from datetime import datetime, timedelta
from pathlib import Path

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
    monkeypatch.setattr(run_ingest, "default_report_output_dir", lambda: Path(".tmp/test-reports"))
    monkeypatch.setattr(
        run_ingest,
        "write_ingest_report",
        lambda report, output_dir: output_dir / "ingest-report-test.json",
    )

    run_ingest.main()

    captured = capsys.readouterr()
    assert "[academic_notices] raw_documents=3 documents=2" in captured.out
    assert "exact_duplicates_removed=1" in captured.out
    assert "version_duplicates_removed=0" in captured.out
    assert "chunks=4 embedded_chunks=2" in captured.out
    assert "total_documents=2" in captured.out
    assert "total_chunks=4" in captured.out
    assert "total_embedded_chunks=2" in captured.out
    assert "ingest_report=.tmp\\test-reports\\ingest-report-test.json" in captured.out


def test_load_sources_config_expands_generated_sources() -> None:
    config_path = Path(".tmp/generated-sources-test.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        config_path.write_text(
            json.dumps(
                {
                    "sources": [{"name": "explicit_source", "seed_urls": ["https://example.com/a"]}],
                    "department_sites": [
                        {
                            "slug": "example_department",
                            "department": "example_department",
                            "base_url": "https://example.com/index.do",
                            "site_type": "portal",
                        }
                    ],
                    "source_blueprints": [
                    {
                        "name_suffix": "notice",
                        "applies_to": ["portal"],
                        "category": "notice",
                        "seed_url_template": "{base_url}/notice",
                        "follow_patterns": ["selectbbsnttlist.do", "selectbbsnttview.do"],
                        "collect_patterns": ["selectbbsnttview.do"],
                    }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        sources = run_ingest.load_sources_config(config_path)

        assert [source["name"] for source in sources] == [
            "explicit_source",
            "example_department_notice",
        ]
        assert sources[1]["department"] == "example_department"
        assert sources[1]["seed_urls"] == ["https://example.com/index.do/notice"]
    finally:
        config_path.unlink(missing_ok=True)


def test_load_sources_config_applies_site_source_overrides() -> None:
    config_path = Path(".tmp/generated-sources-override-test.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        config_path.write_text(
            json.dumps(
                {
                    "department_sites": [
                        {
                            "slug": "example_department",
                            "department": "example_department",
                            "base_url": "https://example.com/index.do",
                            "site_type": "portal",
                            "source_overrides": {
                                "faq": {
                                    "seed_urls": ["https://example.com/faq"],
                                    "collect_seed_pages": True,
                                    "collect_patterns": ["faq"],
                                }
                            },
                        }
                    ],
                    "source_blueprints": [
                        {
                            "name_suffix": "faq",
                            "applies_to": ["portal"],
                            "category": "faq",
                            "seed_url_template": "{base_url}/faq-default",
                            "collect_seed_pages": False,
                            "collect_patterns": ["selectbbsnttview.do"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        sources = run_ingest.load_sources_config(config_path)

        assert [source["name"] for source in sources] == ["example_department_faq"]
        assert sources[0]["seed_urls"] == ["https://example.com/faq"]
        assert sources[0]["collect_seed_pages"] is True
        assert sources[0]["collect_patterns"] == ["faq"]
    finally:
        config_path.unlink(missing_ok=True)


def test_build_crawler_config_derives_allowed_path_prefixes_and_skip_images() -> None:
    config = run_ingest.build_crawler_config(
        {
            "seed_urls": ["https://www.kyonggi.ac.kr/open_major_Seoul/selectBbsNttList.do?key=1"],
            "category": "notice",
            "department": "open_major_seoul",
            "skip_images": True,
            "allowed_author_department_filters": ["자유전공"],
        }
    )

    assert config.allowed_path_prefixes == ("/open_major_Seoul/",)
    assert config.docling_config.skip_images is True
    assert config.allowed_author_department_filters == ("자유전공",)
