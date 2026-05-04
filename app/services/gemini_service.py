from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai

from app.core.config import settings


_APP_TIMEZONE = ZoneInfo("Asia/Seoul")


def _current_context() -> str:
    now = datetime.now(_APP_TIMEZONE)
    return (
        "Runtime context:\n"
        f"- Current date: {now.date().isoformat()}\n"
        f"- Current time: {now.strftime('%H:%M:%S %Z')}\n"
        "- Timezone: Asia/Seoul\n"
        "- Treat dates before the current date as past, the current date as present, "
        "and dates after the current date as future.\n"
        "- Do not use the model training cutoff as today's date.\n"
        "- For weather forecasts or current weather, do not invent live weather data. "
        "If no weather data source is provided, explain that real-time weather data is required.\n"
    )


def _with_current_context(prompt: str) -> str:
    return f"{_current_context()}\nUser/task prompt:\n{prompt}"


def _call_gemini(prompt: str) -> str:
    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_with_current_context(prompt)
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


def get_gemini_response_with_context(user_input: str, context: str) -> str:
    prompt = f"""
You are a helpful university assistant.
Answer the user's question using only the information in the context.
If the context does not contain enough information, say that the available
information is insufficient and ask for a more specific question.

Context:
{context}

User question:
{user_input}

Answer:
"""
    return _call_gemini(prompt)



