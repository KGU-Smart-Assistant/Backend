from types import SimpleNamespace

from app.crawlers.parsing.parser_router import ParserRouter
from app.crawlers.parsing.schemas import ParseContext


def test_parser_router_uses_faq_parser_for_faq_category() -> None:
    router = ParserRouter()
    result = SimpleNamespace(
        markdown=SimpleNamespace(fit_markdown="FAQ\n총게시물 : 0\n질문 답변 검색"),
        metadata={"title": "FAQ - 예시학과"},
    )

    parsed = router.parse(
        result=result,
        context=ParseContext(
            url="https://example.com/selectBbsNttList.do?bbsNo=950",
            category="faq",
            department="example",
        ),
    )

    assert parsed is None


def test_parser_router_keeps_non_empty_faq_list_page() -> None:
    router = ParserRouter()
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown="FAQ\n질문 답변 검색\n휴학은 어디서 신청하나요?\n학과 사무실 방문"
        ),
        metadata={"title": "FAQ - 예시학과"},
    )

    parsed = router.parse(
        result=result,
        context=ParseContext(
            url="https://example.com/selectBbsNttList.do?bbsNo=950",
            category="faq",
            department="example",
        ),
    )

    assert parsed is not None
    assert parsed.title == "FAQ - 예시학과"
    assert parsed.content == "휴학은 어디서 신청하나요?\n학과 사무실 방문"


def test_parser_router_uses_schedule_parser_for_schedule_category() -> None:
    router = ParserRouter()
    result = SimpleNamespace(
        markdown=SimpleNamespace(fit_markdown="2026년 4월 학사일정"),
        metadata={"title": "학사일정 - 예시학과"},
    )

    parsed = router.parse(
        result=result,
        context=ParseContext(
            url="https://example.com/selectTnSchafsSchdulListUS.do?key=1",
            category="academic_schedule",
            department="example",
        ),
    )

    assert parsed is not None
    assert parsed.title == "학사일정 - 예시학과"


def test_parser_router_applies_site_specific_parser_options() -> None:
    router = ParserRouter()
    result = SimpleNamespace(
        markdown=SimpleNamespace(
            fit_markdown="* 경기대학교\n2025학년도 협력병원 건강검진 안내드립니다."
        ),
        metadata={"title": "* 경기대학교"},
        links={"internal": []},
    )

    parsed = router.parse(
        result=result,
        context=ParseContext(
            url="https://www.kyonggi.ac.kr/u_tour/selectBbsNttView.do?bbsNo=684&nttNo=1",
            category="materials",
            department="tourism_culture_college",
        ),
    )

    assert parsed is not None
    assert parsed.title == "2025학년도 협력병원 건강검진 안내드립니다."
