from app.crawlers.crawl4ai_collector import (
    Crawl4AICollectorConfig,
    _build_html_document,
    _html_url_priority,
    _is_allowed_url,
    _normalize_url,
    _should_collect_html_url,
)
from datetime import datetime
from types import SimpleNamespace


def test_should_collect_html_url_uses_collect_patterns() -> None:
    config = Crawl4AICollectorConfig(
        seed_urls=["https://example.com/board"],
        include_patterns=("selectbbsnttlist.do", "selectbbsnttview.do"),
        collect_patterns=("selectbbsnttview.do",),
    )

    assert _should_collect_html_url(
        "https://example.com/selectBbsNttView.do?bbsNo=1",
        config=config,
        is_seed=False,
    )
    assert not _should_collect_html_url(
        "https://example.com/selectBbsNttList.do?bbsNo=1",
        config=config,
        is_seed=True,
    )


def test_should_collect_html_url_can_skip_seed_pages() -> None:
    config = Crawl4AICollectorConfig(
        seed_urls=["https://example.com/board"],
        include_patterns=("selectbbsnttlist.do",),
        collect_seed_pages=False,
    )

    assert not _should_collect_html_url(
        "https://example.com/selectBbsNttList.do?bbsNo=1",
        config=config,
        is_seed=True,
    )


def test_is_allowed_url_uses_follow_patterns_for_html() -> None:
    config = Crawl4AICollectorConfig(
        seed_urls=["https://example.com/board"],
        include_patterns=("contents.do",),
        follow_patterns=("selectbbsnttlist.do", "selectbbsnttview.do"),
    )

    allowed_domains = {"example.com"}

    assert _is_allowed_url(
        "https://example.com/selectBbsNttList.do?bbsNo=1",
        allowed_domains=allowed_domains,
        config=config,
    )
    assert _is_allowed_url(
        "https://example.com/selectBbsNttView.do?bbsNo=1&nttNo=2",
        allowed_domains=allowed_domains,
        config=config,
    )
    assert not _is_allowed_url(
        "https://example.com/contents.do?key=123",
        allowed_domains=allowed_domains,
        config=config,
    )


def test_is_allowed_url_restricts_html_to_allowed_path_prefixes() -> None:
    config = Crawl4AICollectorConfig(
        seed_urls=["https://example.com/open_major/index.do"],
        follow_patterns=("selectbbsnttview.do",),
        allowed_path_prefixes=("/open_major/",),
    )

    assert _is_allowed_url(
        "https://example.com/open_major/selectBbsNttView.do?bbsNo=1&nttNo=2",
        allowed_domains={"example.com"},
        config=config,
    )
    assert not _is_allowed_url(
        "https://example.com/www/selectBbsNttView.do?bbsNo=1073&nttNo=9",
        allowed_domains={"example.com"},
        config=config,
    )


def test_is_allowed_url_still_allows_document_links() -> None:
    config = Crawl4AICollectorConfig(
        seed_urls=["https://example.com/board"],
        follow_patterns=("selectbbsnttlist.do",),
        allowed_path_prefixes=("/board/",),
    )

    assert _is_allowed_url(
        "https://example.com/files/notice.pdf",
        allowed_domains={"example.com"},
        config=config,
    )


def test_is_allowed_url_does_not_block_searchcnd_query() -> None:
    config = Crawl4AICollectorConfig(
        seed_urls=["https://example.com/board"],
        follow_patterns=("selectbbsnttview.do",),
    )

    assert _is_allowed_url(
        "https://example.com/selectBbsNttView.do?bbsNo=1&searchCnd=all",
        allowed_domains={"example.com"},
        config=config,
    )


def test_normalize_url_removes_jsessionid_segment() -> None:
    normalized = _normalize_url(
        "https://example.com/selectBbsNttView.do;jsessionid=ABC123?bbsNo=1&nttNo=2"
    )

    assert normalized == "https://example.com/selectBbsNttView.do?bbsNo=1&nttNo=2"


def test_normalize_url_sorts_query_parameters() -> None:
    normalized = _normalize_url(
        "https://example.com/selectTnSchafsSchdulListUS.do?sa1=u_ai&sc1=10&key=9044"
    )

    assert normalized == (
        "https://example.com/selectTnSchafsSchdulListUS.do?key=9044&sa1=u_ai&sc1=10"
    )


def test_html_url_priority_prefers_board_details() -> None:
    urls = [
        "https://example.com/contents.do?key=1",
        "https://example.com/selectBbsNttList.do?bbsNo=1",
        "https://example.com/selectBbsNttView.do?bbsNo=1&nttNo=2",
    ]

    ordered = sorted(urls, key=_html_url_priority)

    assert ordered == [
        "https://example.com/selectBbsNttView.do?bbsNo=1&nttNo=2",
        "https://example.com/selectBbsNttList.do?bbsNo=1",
        "https://example.com/contents.do?key=1",
    ]


def test_build_html_document_extracts_metadata_from_board_detail() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown=(
                "[대학생활/업무안내] 2026년 2월 졸업예정자 졸업논문 안내\n\n"
                "_작성자_ 청소년학전공\n"
                "_작성일_ 2025년 08월 11일 10시 29분 00초\n"
                "첨부파일 다운로드"
            )
        ),
        metadata={"title": "공지사항 - 청소년학전공"},
        links={
            "internal": [
                {"href": "/files/plan.pdf"},
                {"href": "/downloadBbsFile.do?atchmnflNo=123"},
            ]
        },
    )

    document = _build_html_document(
        url="https://example.com/selectBbsNttView.do?nttNo=1",
        result=result,
        category="notice",
        department="youth",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
    )

    assert document is not None
    assert document.title == "2026년 2월 졸업예정자 졸업논문 안내"
    assert document.author_department == "청소년학전공"
    assert document.published_at == datetime(2025, 8, 11, 10, 29, 0)
    assert document.attachment_urls == [
        "https://example.com/files/plan.pdf",
        "https://example.com/downloadBbsFile.do?atchmnflNo=123",
    ]


def test_build_html_document_sanitizes_malformed_markdown_titles() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown=(
                "[본문 바로가기](https://example.com/skip)\n"
                "제100차 한국관광학회 안내](https://example.com/detail)\n"
            )
        ),
        metadata={"title": "자료실 - 예시학과"},
        links={"internal": []},
    )

    document = _build_html_document(
        url="https://example.com/selectBbsNttView.do?nttNo=2",
        result=result,
        category="materials",
        department="example",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
    )

    assert document is not None
    assert document.title == "제100차 한국관광학회 안내"


def test_build_html_document_skips_empty_faq_page() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown="FAQ\n총게시물 : 0\n질문 답변 검색"
        ),
        metadata={"title": "FAQ - 예시학과"},
        links={"internal": []},
    )

    document = _build_html_document(
        url="https://example.com/selectBbsNttList.do?bbsNo=950",
        result=result,
        category="faq",
        department="example",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
    )

    assert document is None


def test_build_html_document_skips_faq_list_page_without_detail_parsing() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown="FAQ\n질문 답변 검색\n예시 질문"
        ),
        metadata={"title": "FAQ - 예시학과"},
        links={"internal": []},
    )

    document = _build_html_document(
        url="https://example.com/selectBbsNttList.do?bbsNo=950",
        result=result,
        category="faq",
        department="example",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
    )

    assert document is None


def test_build_html_document_applies_keyword_filters() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown=(
                "2026학년도 전공자율선택제 신입생 설명회 발표자료\n"
                "_작성자_ 전공설계융합팀\n"
            )
        ),
        metadata={"title": "자료실 - 예시학과"},
        links={"internal": []},
    )

    accepted = _build_html_document(
        url="https://example.com/selectBbsNttView.do?nttNo=3",
        result=result,
        category="materials",
        department="example",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
        allowed_keyword_filters=("전공설계융합",),
    )
    rejected = _build_html_document(
        url="https://example.com/selectBbsNttView.do?nttNo=4",
        result=result,
        category="materials",
        department="example",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
        allowed_keyword_filters=("인공지능",),
    )

    assert accepted is not None
    assert rejected is None


def test_build_html_document_applies_blocked_keyword_filters() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown=(
                "[산업경영공학과] 시험불참신고서 양식\n"
                "_작성자_ 산업경영공학과\n"
            )
        ),
        metadata={"title": "자료실 - 예시학과"},
        links={"internal": []},
    )

    document = _build_html_document(
        url="https://example.com/selectBbsNttView.do?nttNo=5",
        result=result,
        category="materials",
        department="example",
        collected_at=datetime(2026, 4, 29, 12, 0, 0),
        blocked_keyword_filters=("산업경영공학과",),
    )

    assert document is None
