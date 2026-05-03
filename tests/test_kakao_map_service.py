import pytest

from app.services.kakao_map_service import (
    KakaoMapConfigurationError,
    KakaoMapService,
)


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_search_keyword_calls_kakao_local_api(monkeypatch):
    captured = {}

    def fake_get(url, *, headers, params, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse({"meta": {"total_count": 0}, "documents": []})

    monkeypatch.setattr("app.services.kakao_map_service.httpx.get", fake_get)

    service = KakaoMapService(
        api_key="test-key",
        base_url="https://dapi.kakao.com",
        timeout=3.0,
    )
    result = service.search_keyword(
        "library",
        x=127.03645,
        y=37.30125,
        radius=1000,
        page=2,
        size=10,
    )

    assert result == {"meta": {"total_count": 0}, "documents": []}
    assert captured["url"] == "https://dapi.kakao.com/v2/local/search/keyword.json"
    assert captured["headers"] == {"Authorization": "KakaoAK test-key"}
    assert captured["params"] == {
        "query": "library",
        "x": 127.03645,
        "y": 37.30125,
        "radius": 1000,
        "page": 2,
        "size": 10,
    }
    assert captured["timeout"] == 3.0


def test_search_address_requires_api_key(monkeypatch):
    monkeypatch.setattr("app.services.kakao_map_service.settings.kakao_rest_api_key", None)
    monkeypatch.setattr("app.services.kakao_map_service.settings.kakao_map_api_key", None)

    service = KakaoMapService(api_key=None)

    with pytest.raises(KakaoMapConfigurationError):
        service.search_address("Suwon")
