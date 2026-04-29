from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.orm import Session

from app.schemas.search import SearchResult
from app.services.call_service import get_phone
from app.services.gemini_service import (
    get_gemini_response,
    get_gemini_response_with_context,
)
from app.services.map_service import get_map_response
from app.services.search_service import search_documents
from app.services.weather_service import get_weather_response

ChatRoute = Literal["llm", "relational_db", "rag", "weather"]
DbIntent = Literal["map", "phone", "unknown"]


@dataclass(frozen=True)
class ChatDecision:
    route: ChatRoute
    db_intent: DbIntent = "unknown"
    reason: str = ""


@dataclass(frozen=True)
class ChatSource:
    type: str
    title: str
    source_url: str | None = None
    score: float | None = None


@dataclass(frozen=True)
class ChatResult:
    reply: str
    intent: str
    route: ChatRoute
    sources: list[ChatSource] = field(default_factory=list)


_PHONE_KEYWORDS = ("전화", "전화번호", "연락처", "문의", "번호")
_MAP_KEYWORDS = (
    "어디",
    "위치",
    "찾아",
    "가는 길",
    "어딘",
    "어디어",
    "도서관",
    "학생회관",
    "강의동",
    "공학관",
    "정문",
    "후문",
    "복지관",
    "박물관",
)
_RAG_KEYWORDS = (
    "공지",
    "안내문",
    "문서",
    "자료",
    "규정",
    "학사",
    "장학",
    "모집",
    "신청",
    "일정",
    "기간",
    "졸업",
    "수강",
    "등록",
    "휴학",
    "복학",
)
_WEATHER_KEYWORDS = (
    "날씨",
    "기온",
    "비 와",
    "비가",
    "비올",
    "비 올",
    "눈 와",
    "눈이",
    "눈올",
    "눈 올",
    "강수",
    "우산",
    "예보",
    "덥",
    "춥",
    "추워",
    "더워",
)


def answer_chat(user_input: str, db: Session) -> ChatResult:
    decision = decide_chat_route(user_input)

    if decision.route == "relational_db":
        return _answer_from_relational_db(user_input, decision, db)

    if decision.route == "rag":
        return _answer_from_rag(user_input)

    if decision.route == "weather":
        return _answer_from_weather(user_input)

    return ChatResult(
        reply=get_gemini_response(user_input),
        intent="일반",
        route="llm",
    )


def decide_chat_route(user_input: str) -> ChatDecision:
    heuristic = _heuristic_decision(user_input)
    if heuristic.route != "llm":
        return heuristic

    prompt = f"""
You classify a user question for a university assistant.
Return only valid JSON with this schema:
{{"route":"llm|relational_db|rag|weather","db_intent":"map|phone|unknown","reason":"short reason"}}

Routing rules:
- llm: basic general knowledge or casual conversation that does not need local data.
- relational_db: exact campus data stored in relational DB, such as place locations or phone numbers.
- rag: information that must be grounded in crawled documents, notices, policies, schedules, or other text sources.
- weather: current or forecast weather questions that need live weather API data.

User question:
{user_input}
"""
    raw = get_gemini_response(prompt)
    parsed = _parse_decision(raw)
    if parsed is None:
        return heuristic
    return parsed


def _answer_from_relational_db(
    user_input: str,
    decision: ChatDecision,
    db: Session,
) -> ChatResult:
    db_intent = decision.db_intent
    if db_intent == "unknown":
        db_intent = _infer_db_intent(user_input)

    if db_intent == "phone":
        reply = get_phone(user_input, db)
        source_title = "kgu_contacts"
        intent = "전화"
    elif db_intent == "map":
        reply = get_map_response(user_input, db)
        source_title = "kgu_places"
        intent = "지도"
    else:
        reply = (
            "확실한 DB 정보가 필요한 질문으로 판단했지만, 어떤 DB에서 찾을지 "
            "결정하지 못했습니다. 장소 위치나 전화번호처럼 더 구체적으로 질문해 주세요."
        )
        source_title = "relational_db"
        intent = "DB"

    return ChatResult(
        reply=reply,
        intent=intent,
        route="relational_db",
        sources=[ChatSource(type="relational_db", title=source_title)],
    )


def _answer_from_rag(user_input: str) -> ChatResult:
    try:
        results = search_documents(query=user_input, top_k=5)
    except NotImplementedError:
        return ChatResult(
            reply=(
                "이 질문은 문서 기반 검색(RAG)으로 답변해야 하지만, 현재 검색 파이프라인이 "
                "아직 연결되어 있지 않습니다. `app/services/search_service.py`에 벡터 검색 "
                "구현이 연결되면 수집 문서를 근거로 답변할 수 있습니다."
            ),
            intent="RAG",
            route="rag",
        )

    if not results:
        return ChatResult(
            reply="관련 문서를 찾지 못했습니다. 질문을 더 구체적으로 입력해 주세요.",
            intent="RAG",
            route="rag",
        )

    context = _format_rag_context(results)
    reply = get_gemini_response_with_context(user_input=user_input, context=context)
    sources = [
        ChatSource(
            type="document",
            title=result.title,
            source_url=result.source_url,
            score=result.score,
        )
        for result in results
    ]
    return ChatResult(reply=reply, intent="RAG", route="rag", sources=sources)


def _answer_from_weather(user_input: str) -> ChatResult:
    report = get_weather_response(user_input)
    return ChatResult(
        reply=report.reply,
        intent="날씨",
        route="weather",
        sources=[
            ChatSource(
                type="weather_api",
                title=f"Open-Meteo forecast: {report.location_name}",
                source_url=report.source_url,
            )
        ],
    )


def _heuristic_decision(user_input: str) -> ChatDecision:
    if any(keyword in user_input for keyword in _WEATHER_KEYWORDS):
        return ChatDecision(route="weather", reason="weather keyword")
    if any(keyword in user_input for keyword in _PHONE_KEYWORDS):
        return ChatDecision(route="relational_db", db_intent="phone", reason="phone keyword")
    if any(keyword in user_input for keyword in _MAP_KEYWORDS):
        return ChatDecision(route="relational_db", db_intent="map", reason="map keyword")
    if any(keyword in user_input for keyword in _RAG_KEYWORDS):
        return ChatDecision(route="rag", reason="document keyword")
    return ChatDecision(route="llm", reason="default")


def _infer_db_intent(user_input: str) -> DbIntent:
    if any(keyword in user_input for keyword in _PHONE_KEYWORDS):
        return "phone"
    if any(keyword in user_input for keyword in _MAP_KEYWORDS):
        return "map"
    return "unknown"


def _parse_decision(raw: str) -> ChatDecision | None:
    if not raw:
        return None

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return None

    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    route = payload.get("route")
    db_intent = payload.get("db_intent", "unknown")
    reason = str(payload.get("reason", ""))

    if route not in {"llm", "relational_db", "rag", "weather"}:
        return None
    if db_intent not in {"map", "phone", "unknown"}:
        db_intent = "unknown"

    return ChatDecision(route=route, db_intent=db_intent, reason=reason)


def _format_rag_context(results: list[SearchResult]) -> str:
    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(
            "\n".join(
                [
                    f"[{index}] {result.title}",
                    f"source_url: {result.source_url}",
                    f"score: {result.score}",
                    result.text,
                ]
            )
        )
    return "\n\n".join(blocks)
