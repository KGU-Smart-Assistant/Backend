import os

os.environ.setdefault("GOOGLE_API_KEY", "test-key")

from app.services import weather_service


def test_weather_service_fetches_open_meteo_and_builds_context(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "daily": {
                    "time": ["2026-04-29", "2026-04-30"],
                    "weather_code": [3, 61],
                    "temperature_2m_max": [20.0, 18.0],
                    "temperature_2m_min": [10.0, 9.0],
                    "precipitation_probability_max": [20, 80],
                    "precipitation_sum": [0.0, 4.2],
                    "wind_speed_10m_max": [12.0, 18.0],
                }
            }

    def fake_get(url: str, *, params: dict, timeout: int):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    def fake_answer(user_input: str, context: str) -> str:
        captured["user_input"] = user_input
        captured["context"] = context
        return "내일 수원은 약한 비가 예상됩니다."

    monkeypatch.setattr(weather_service.requests, "get", fake_get)
    monkeypatch.setattr(weather_service, "get_gemini_response_with_context", fake_answer)
    monkeypatch.setattr(weather_service, "_extract_forecast_window", lambda _: (weather_service.date(2026, 4, 30), 1))

    report = weather_service.get_weather_response("내일 수원 날씨 알려줘")

    assert report.reply == "내일 수원은 약한 비가 예상됩니다."
    assert report.location_name == "수원"
    assert captured["url"] == "https://api.open-meteo.com/v1/forecast"
    assert captured["params"]["timezone"] == "Asia/Seoul"
    assert captured["params"]["latitude"] == 37.2636
    assert "2026-04-30" in captured["context"]
    assert "약한 비" in captured["context"]
    assert "precipitation probability 80%" in captured["context"]
