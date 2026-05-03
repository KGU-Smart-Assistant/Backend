from pydantic import BaseModel, Field


class KakaoSearchMeta(BaseModel):
    total_count: int = 0
    pageable_count: int = 0
    is_end: bool = True


class KakaoPlace(BaseModel):
    id: str
    place_name: str
    category_name: str | None = None
    address_name: str | None = None
    road_address_name: str | None = None
    phone: str | None = None
    place_url: str | None = None
    x: float = Field(description="Longitude")
    y: float = Field(description="Latitude")
    distance: str | None = None


class KakaoKeywordSearchResponse(BaseModel):
    meta: KakaoSearchMeta
    documents: list[KakaoPlace]


class KakaoAddress(BaseModel):
    address_name: str
    x: float = Field(description="Longitude")
    y: float = Field(description="Latitude")
    address_type: str | None = None


class KakaoAddressSearchResponse(BaseModel):
    meta: KakaoSearchMeta
    documents: list[KakaoAddress]
