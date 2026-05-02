import zipfile
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


class _FailingConverter:
    def convert(self, source, headers=None):
        raise RuntimeError("conversion failed")


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


def test_collect_documents_with_docling_extracts_hwpx_text(tmp_path) -> None:
    hwpx_path = tmp_path / "sample.hwpx"
    with zipfile.ZipFile(hwpx_path, "w") as archive:
        archive.writestr(
            "Contents/section0.xml",
            "<root><p>입체조형학과</p><p>실험실습비 사용내역</p></root>",
        )

    documents = collect_documents_with_docling([str(hwpx_path)])

    assert len(documents) == 1
    assert documents[0].source_type == "hwpx"
    assert "입체조형학과" in documents[0].content
    assert "실험실습비 사용내역" in documents[0].content


def test_collect_documents_with_docling_extracts_supported_zip_members(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(
        "app.crawlers.docling_collector._create_converter",
        lambda: _FakeConverter(),
    )
    zip_path = tmp_path / "attachments.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("notice.pdf", b"%PDF")
        archive.writestr("ignore.txt", "not collected")

    documents = collect_documents_with_docling([str(zip_path)])

    assert len(documents) == 1
    assert documents[0].source_type == "pdf"
    assert documents[0].source_url.endswith("#notice.pdf")


def test_collect_documents_with_docling_skips_failed_conversions(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.crawlers.docling_collector._create_converter",
        lambda: _FailingConverter(),
    )

    documents = collect_documents_with_docling(["https://example.com/file.pdf"])

    assert documents == []
