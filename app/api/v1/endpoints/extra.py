from fastapi import APIRouter

router = APIRouter()

# 1. 캠퍼스 강의동 지도 & 경로 안내
@router.get("/map/navigation")
async def get_campus_navigation():
    # 카카오맵 API 연동 로직
    return {"message": "지도 경로 안내 기능을 준비 중입니다."}

# 2. 부서 전화번호 목록
@router.get("/contacts")
async def get_department_contacts():
    # 부서별 전화번호 리스트 (임시 데이터)
    return {
        "학사지원팀": "031-249-0000",
        "학생지원팀": "031-249-1111",
        "입학관리팀": "031-249-2222"
    }

# 3. 다국어 지원 관련 (현재 언어 설정 확인 등)
@router.get("/language-settings")
async def get_language_settings():
    return {"supported_languages": ["ko", "en", "ja"]}