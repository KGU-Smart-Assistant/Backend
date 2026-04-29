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
