from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("--- 사용 가능한 모델 목록 확인 중 ---")
try:
    for m in client.models.list():
        # 'supported_methods'로 속성명을 변경했습니다.
        if 'generateContent' in m.supported_methods:
            print(f"사용 가능 모델명: {m.name}")
except Exception as e:
    # 만약 위 방법도 에러가 난다면, 그냥 모든 모델 이름을 다 출력하게 합니다.
    print(f"필터링 에러 발생 시 전체 출력 시도 중...")
    for m in client.models.list():
        print(f"모델명: {m.name}")