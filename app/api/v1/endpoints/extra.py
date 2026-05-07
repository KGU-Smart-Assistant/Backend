from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.schemas.contact import DepartmentContact, DepartmentContactListResponse
from app.schemas.map import MapNavigationResponse
from app.services.contact_service import get_department_contact, list_department_contacts
from app.services.kakao_map_service import KakaoMapServiceError, get_navigation_route

router = APIRouter()


@router.get("/map/navigation", response_model=MapNavigationResponse)
async def get_campus_navigation(
    origin: str = Query(..., min_length=1, description="Start place keyword"),
    destination: str = Query(..., min_length=1, description="End place keyword"),
):
    if not settings.kakao_map_api_key:
        raise HTTPException(status_code=500, detail="KAKAO_MAP_API_KEY is not configured")

    try:
        return await get_navigation_route(
            api_key=settings.kakao_map_api_key,
            origin=origin,
            destination=destination,
        )
    except KakaoMapServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/contacts", response_model=DepartmentContactListResponse)
async def get_department_contacts() -> DepartmentContactListResponse:
    return DepartmentContactListResponse(contacts=list_department_contacts())


@router.get("/contacts/{department_id}", response_model=DepartmentContact)
async def get_department_contact_by_id(department_id: str) -> DepartmentContact:
    contact = get_department_contact(department_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Department contact not found")
    return DepartmentContact(**contact)


@router.get("/language-settings")
async def get_language_settings():
    return {"supported_languages": ["ko", "en", "ja"]}
