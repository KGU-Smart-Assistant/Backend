"""Crawler and document collection utilities."""

__all__ = [
    "Crawl4AICollectorConfig",
    "collect_documents_with_crawl4ai",
    "DoclingCollectorConfig",
    "collect_documents_with_docling",
]


def __getattr__(name: str):
    if name in {"Crawl4AICollectorConfig", "collect_documents_with_crawl4ai"}:
        from app.crawlers.crawl4ai_collector import (
            Crawl4AICollectorConfig,
            collect_documents_with_crawl4ai,
        )

        exports = {
            "Crawl4AICollectorConfig": Crawl4AICollectorConfig,
            "collect_documents_with_crawl4ai": collect_documents_with_crawl4ai,
        }
        return exports[name]

    if name in {"DoclingCollectorConfig", "collect_documents_with_docling"}:
        from app.crawlers.docling_collector import (
            DoclingCollectorConfig,
            collect_documents_with_docling,
        )

        exports = {
            "DoclingCollectorConfig": DoclingCollectorConfig,
            "collect_documents_with_docling": collect_documents_with_docling,
        }
        return exports[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
