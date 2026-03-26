from google import genai
from app.core.config import settings



def get_gemini_response(user_input: str) -> str:
    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model="models/gemini-2.5-flash-lite", 
            contents=user_input
        )
        
        if response and response.text:
            return response.text
        return "응답은 성공했으나 텍스트가 없습니다."

    except Exception as e:
        error_msg = str(e)
        # 터미널에 에러 원인을 아주 크게 출력합니다.
        print("\n" + "="*50)
        print(f"GEMINI ERROR: {error_msg}")
        print("="*50 + "\n")
        
        if "429" in error_msg:
            return "현재 사용량이 너무 많아 구글이 차단했습니다. 1분만 쉬었다가 다시 눌러보세요."
        elif "404" in error_msg:
            return "모델 이름을 찾을 수 없습니다. (2.0-flash-lite 재시도 필요)"
        return f"서버 에러가 발생했습니다: {error_msg}"
        return f"서버 내부 에러가 발생했습니다: {str(e)}"