from types import SimpleNamespace

from app.crawlers.docling_collector import (
    DoclingCollectorConfig,
    collect_documents_with_docling,
)


class _FakeConverter:
    def convert(self, source, headers=None):
        return SimpleNamespace(
            document=SimpleNamespace(export_to_markdown=lambda: "# Example\ncontent")
        )


def test_collect_documents_with_docling_skips_images_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.crawlers.docling_collector._create_converter",
        lambda: _FakeConverter(),
    )

    documents = collect_documents_with_docling(
        ["https://example.com/file.png"],
        config=DoclingCollectorConfig(skip_images=True),
    )

    assert documents == []


def test_collect_documents_with_docling_keeps_non_image_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.crawlers.docling_collector._create_converter",
        lambda: _FakeConverter(),
    )

    documents = collect_documents_with_docling(
        ["https://example.com/file.pdf"],
        config=DoclingCollectorConfig(skip_images=True),
    )

    assert len(documents) == 1
    assert documents[0].source_type == "pdf"
