from typing import List, Optional

from app.schemas import SearchResponse, SearchResult


def search_documents(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
) -> List[SearchResult]:
    """Return the most relevant document chunks for a query.

    This service interface is fixed first so the crawler, chunker,
    embedder, and vector store can all target the same contract.
    """
    raise NotImplementedError("Search pipeline is not implemented yet.")


def search(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
) -> SearchResponse:
    """Wrap raw search results in the standard response schema."""
    results = search_documents(query=query, top_k=top_k, category=category)
    return SearchResponse(query=query, results=results)
