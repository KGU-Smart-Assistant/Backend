from typing import Any

import httpx


KAKAO_LOCAL_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"


class KakaoMapServiceError(Exception):
    pass


def _auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"KakaoAK {api_key}",
        "Content-Type": "application/json",
    }


async def search_place(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    query: str,
    x: str | None = None,
    y: str | None = None,
    radius: int | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"query": query, "size": 1}
    if x is not None and y is not None:
        params["x"] = x
        params["y"] = y
    if radius is not None:
        params["radius"] = radius

    response = await client.get(
        KAKAO_LOCAL_KEYWORD_URL,
        headers=_auth_headers(api_key),
        params=params,
    )
    if response.status_code >= 400:
        raise KakaoMapServiceError(
            f"Kakao place search failed with status {response.status_code}"
        )

    payload = response.json()
    documents = payload.get("documents", [])
    if not documents:
        raise KakaoMapServiceError(f"No Kakao place found for query: {query}")

    return documents[0]


async def get_driving_directions(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    origin_x: str,
    origin_y: str,
    destination_x: str,
    destination_y: str,
) -> dict[str, Any]:
    response = await client.get(
        KAKAO_DIRECTIONS_URL,
        headers=_auth_headers(api_key),
        params={
            "origin": f"{origin_x},{origin_y}",
            "destination": f"{destination_x},{destination_y}",
            "priority": "RECOMMEND",
        },
    )
    if response.status_code >= 400:
        raise KakaoMapServiceError(
            f"Kakao directions failed with status {response.status_code}"
        )

    return response.json()


async def get_navigation_route(
    *,
    api_key: str,
    origin: str,
    destination: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        origin_place = await search_place(client, api_key=api_key, query=origin)
        destination_place = await search_place(
            client,
            api_key=api_key,
            query=destination,
            x=origin_place.get("x"),
            y=origin_place.get("y"),
            radius=20000,
        )
        directions = await get_driving_directions(
            client,
            api_key=api_key,
            origin_x=origin_place["x"],
            origin_y=origin_place["y"],
            destination_x=destination_place["x"],
            destination_y=destination_place["y"],
        )

    return {
        "origin": origin_place,
        "destination": destination_place,
        "directions": directions,
    }
