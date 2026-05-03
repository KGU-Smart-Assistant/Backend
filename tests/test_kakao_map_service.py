import httpx
import pytest

from app.services.kakao_map_service import (
    KAKAO_DIRECTIONS_URL,
    KAKAO_LOCAL_KEYWORD_URL,
    get_driving_directions,
    search_place,
)


@pytest.mark.anyio
async def test_search_place_calls_kakao_keyword_api() -> None:
    seen_request = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return httpx.Response(
            200,
            json={
                "documents": [
                    {
                        "id": "1",
                        "place_name": "KGU",
                        "address_name": "Suwon",
                        "x": "127.036",
                        "y": "37.300",
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        place = await search_place(client, api_key="test-key", query="KGU")

    assert seen_request is not None
    assert str(seen_request.url).startswith(KAKAO_LOCAL_KEYWORD_URL)
    assert seen_request.headers["Authorization"] == "KakaoAK test-key"
    assert place["place_name"] == "KGU"


@pytest.mark.anyio
async def test_get_driving_directions_calls_kakao_navigation_api() -> None:
    seen_request = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return httpx.Response(200, json={"routes": [{"summary": {"distance": 1200}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        directions = await get_driving_directions(
            client,
            api_key="test-key",
            origin_x="127.036",
            origin_y="37.300",
            destination_x="127.040",
            destination_y="37.305",
        )

    assert seen_request is not None
    assert str(seen_request.url).startswith(KAKAO_DIRECTIONS_URL)
    assert seen_request.headers["Authorization"] == "KakaoAK test-key"
    assert seen_request.url.params["origin"] == "127.036,37.300"
    assert seen_request.url.params["destination"] == "127.040,37.305"
    assert directions["routes"][0]["summary"]["distance"] == 1200
