"""Business logic services."""

__all__ = [
    "chunk_document",
    "chunk_documents",
    "collect_documents_with_crawl4ai",
    "Crawl4AICollectorConfig",
    "DoclingCollectorConfig",
    "collect_documents_with_docling",
    "embed_chunks",
    "embed_text",
    "embed_texts",
    "get_gemini_response",
    "search",
    "search_documents",
]


def __getattr__(name: str):
    if name in {"Crawl4AICollectorConfig", "collect_documents_with_crawl4ai"}:
        from app.services.crawl4ai_collector import (
            Crawl4AICollectorConfig,
            collect_documents_with_crawl4ai,
        )

        exports = {
            "Crawl4AICollectorConfig": Crawl4AICollectorConfig,
            "collect_documents_with_crawl4ai": collect_documents_with_crawl4ai,
        }
        return exports[name]

    if name in {"embed_text", "embed_texts", "embed_chunks"}:
        from app.services.embedding_service import embed_chunks, embed_text, embed_texts

        exports = {
            "embed_text": embed_text,
            "embed_texts": embed_texts,
            "embed_chunks": embed_chunks,
        }
        return exports[name]

    if name in {"chunk_document", "chunk_documents"}:
        from app.services.chunking_service import chunk_document, chunk_documents

        exports = {
            "chunk_document": chunk_document,
            "chunk_documents": chunk_documents,
        }
        return exports[name]

    if name in {"DoclingCollectorConfig", "collect_documents_with_docling"}:
        from app.services.docling_collector import (
            DoclingCollectorConfig,
            collect_documents_with_docling,
        )

        exports = {
            "DoclingCollectorConfig": DoclingCollectorConfig,
            "collect_documents_with_docling": collect_documents_with_docling,
        }
        return exports[name]

    if name == "get_gemini_response":
        from app.services.gemini_service import get_gemini_response

        return get_gemini_response

    if name in {"search", "search_documents"}:
        from app.services.search_service import search, search_documents

        exports = {
            "search": search,
            "search_documents": search_documents,
        }
        return exports[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
