import os
from google import genai
from app.core.config import settings
from app.schemas import SearchResult




def _call_gemini(prompt: str) -> str:
    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model="models/gemini-2.5-flash-lite",
            contents=prompt
        )

        if response and response.text:
            return response.text.strip()
        return ""

    except Exception as e:
        error_msg = str(e)

        print("\n" + "="*50)
        print(f"GEMINI ERROR: {error_msg}")
        print("="*50 + "\n")

        if "429" in error_msg:
            return "현재 사용량이 너무 많아 구글이 차단했습니다. 1분만 쉬었다가 다시 눌러보세요."
        elif "404" in error_msg:
            return "모델 이름을 찾을 수 없습니다. (2.0-flash-lite 재시도 필요)"
        
        return f"서버 에러가 발생했습니다: {error_msg}"



def get_gemini_response(user_input: str) -> str:
    return _call_gemini(user_input)


def get_gemini_response_with_context(
    user_input: str,
    search_results: list[SearchResult],
) -> str:
    context = _format_search_context(search_results)
    prompt = f"""
아래 경기대학교 수집 자료만 근거로 답변하세요.
자료에 없는 내용은 모른다고 답하세요.
신청 기간, 자격, 제출 서류, 금액처럼 자료에 직접 없는 세부사항을 추측하지 마세요.
자료가 부족하면 확인 가능한 공지 제목과 URL을 안내하세요.

참고 자료:
{context}

질문:
{user_input}

답변:
"""
    answer = _call_gemini(prompt)
    if not answer:
        return "관련 자료를 바탕으로 답변을 생성하지 못했습니다."
    return f"{answer}\n\n{_format_sources(search_results)}"


def _format_search_context(search_results: list[SearchResult]) -> str:
    blocks = []
    for index, result in enumerate(search_results, start=1):
        blocks.append(
            "\n".join(
                [
                    f"[자료 {index}]",
                    f"제목: {result.title}",
                    f"URL: {result.source_url}",
                    f"내용: {result.text}",
                ]
            )
        )
    return "\n\n".join(blocks)


def _format_sources(search_results: list[SearchResult]) -> str:
    seen_urls: set[str] = set()
    lines = ["출처:"]
    for result in search_results:
        if result.source_url in seen_urls:
            continue
        seen_urls.add(result.source_url)
        lines.append(f"- {result.title}: {result.source_url}")
    return "\n".join(lines)

