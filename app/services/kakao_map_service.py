from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class KakaoMapServiceError(Exception):
    """Raised when Kakao Local API returns an error or cannot be reached."""


class KakaoMapConfigurationError(KakaoMapServiceError):
    """Raised when Kakao API configuration is missing."""


class KakaoMapService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = settings.kakao_local_base_url,
        timeout: float = 5.0,
    ) -> None:
        self.api_key = (
            api_key
            or settings.kakao_rest_api_key
            or settings.kakao_map_api_key
        )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search_keyword(
        self,
        query: str,
        *,
        x: float | None = None,
        y: float | None = None,
        radius: int | None = None,
        page: int = 1,
        size: int = 15,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "query": query,
            "page": page,
            "size": size,
        }
        if x is not None:
            params["x"] = x
        if y is not None:
            params["y"] = y
        if radius is not None:
            params["radius"] = radius

        return self._get("/v2/local/search/keyword.json", params=params)

    def search_address(
        self,
        query: str,
        *,
        page: int = 1,
        size: int = 10,
    ) -> dict[str, Any]:
        return self._get(
            "/v2/local/search/address.json",
            params={"query": query, "page": page, "size": size},
        )

    def _get(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise KakaoMapConfigurationError(
                "KAKAO_REST_API_KEY or KAKAO_MAP_API_KEY is not configured."
            )

        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers={"Authorization": f"KakaoAK {self.api_key}"},
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise KakaoMapServiceError(
                f"Kakao Local API returned {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise KakaoMapServiceError("Kakao Local API request failed.") from exc

        data = response.json()
        if not isinstance(data, dict):
            raise KakaoMapServiceError("Kakao Local API returned an invalid response.")
        return data
