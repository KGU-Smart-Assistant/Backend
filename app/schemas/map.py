from typing import Any

from pydantic import BaseModel, Field


class KakaoPlace(BaseModel):
    id: str | None = None
    place_name: str
    address_name: str | None = None
    road_address_name: str | None = None
    x: str = Field(description="Longitude")
    y: str = Field(description="Latitude")
    place_url: str | None = None


class MapNavigationResponse(BaseModel):
    origin: KakaoPlace
    destination: KakaoPlace
    directions: dict[str, Any]
