from app.db import vector_store


def test_create_client_uses_http_mode(monkeypatch) -> None:
    calls = {}

    class FakeChroma:
        @staticmethod
        def HttpClient(*, host, port):
            calls["host"] = host
            calls["port"] = port
            return "http-client"

    monkeypatch.setattr(vector_store.settings, "vector_store_mode", "http")
    monkeypatch.setattr(vector_store.settings, "vector_store_host", "chroma")
    monkeypatch.setattr(vector_store.settings, "vector_store_port", 8000)
    monkeypatch.setitem(__import__("sys").modules, "chromadb", FakeChroma)

    assert vector_store._create_client() == "http-client"
    assert calls == {"host": "chroma", "port": 8000}


def test_create_client_rejects_unknown_mode(monkeypatch) -> None:
    class FakeChroma:
        pass

    monkeypatch.setattr(vector_store.settings, "vector_store_mode", "bad-mode")
    monkeypatch.setitem(__import__("sys").modules, "chromadb", FakeChroma)

    try:
        vector_store._create_client()
    except ValueError as exc:
        assert str(exc) == "VECTOR_STORE_MODE must be either 'embedded' or 'http'."
    else:
        raise AssertionError("Expected ValueError for unknown vector store mode.")
