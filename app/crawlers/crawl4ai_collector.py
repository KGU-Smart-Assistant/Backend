import asyncio
import hashlib
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

from app.crawlers.docling_collector import (
    DoclingCollectorConfig,
    collect_documents_with_docling,
)
from app.schemas import Document

DOCUMENT_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tif": "image",
    ".tiff": "image",
    ".bmp": "image",
    ".gif": "image",
    ".webp": "image",
}

DEFAULT_INCLUDE_PATTERNS = (
    "notice",
    "bbs",
    "board",
    "academic",
    "scholarship",
    "faq",
    "download",
    "dn.php",
    "contents.do",
    ".pdf",
    ".docx",
)

DEFAULT_EXCLUDE_PATTERNS = (
    "login",
    "logout",
    "signup",
    "search",
    "javascript:",
    "mailto:",
)


@dataclass
class Crawl4AICollectorConfig:
    seed_urls: List[str]
    max_pages: int = 20
    max_depth: int = 2
    category: Optional[str] = None
    department: Optional[str] = None
    include_patterns: Tuple[str, ...] = DEFAULT_INCLUDE_PATTERNS
    exclude_patterns: Tuple[str, ...] = DEFAULT_EXCLUDE_PATTERNS
    allowed_domains: Optional[Set[str]] = None
    headless: bool = True
    word_count_threshold: int = 1
    page_timeout_ms: int = 30000
    docling_config: DoclingCollectorConfig = field(default_factory=DoclingCollectorConfig)


def collect_documents_with_crawl4ai(
    config: Crawl4AICollectorConfig,
) -> List[Document]:
    """Discover same-domain pages and document links starting from seed URLs."""
    return asyncio.run(_collect_documents_with_crawl4ai(config))


async def _collect_documents_with_crawl4ai(
    config: Crawl4AICollectorConfig,
) -> List[Document]:
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except ImportError as exc:
        raise RuntimeError(
            "crawl4ai is not installed. Add 'crawl4ai' to dependencies and install it first."
        ) from exc

    allowed_domains = config.allowed_domains or {
        _normalize_domain(urlparse(seed).netloc) for seed in config.seed_urls
    }

    browser_config = BrowserConfig(
        headless=config.headless,
        java_script_enabled=True,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=config.word_count_threshold,
        page_timeout=config.page_timeout_ms,
    )

    queue: Deque[Tuple[str, int]] = deque(
        (_normalize_url(url), 0) for url in config.seed_urls
    )
    visited_html_urls: Set[str] = set()
    collected_doc_urls: Set[str] = set()
    documents: List[Document] = []
    collected_at = datetime.now()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and len(visited_html_urls) < config.max_pages:
            current_url, depth = queue.popleft()
            if current_url in visited_html_urls:
                continue
            if not _is_allowed_url(current_url, allowed_domains, config):
                continue

            result = await crawler.arun(url=current_url, config=run_config)
            visited_html_urls.add(current_url)

            if not getattr(result, "success", False):
                continue

            html_document = _build_html_document(
                url=current_url,
                result=result,
                category=config.category,
                department=config.department,
                collected_at=collected_at,
            )
            if html_document is not None:
                documents.append(html_document)

            discovered_html_urls, discovered_doc_urls = _extract_links(
                base_url=current_url,
                result_links=getattr(result, "links", {}) or {},
                allowed_domains=allowed_domains,
                config=config,
            )

            collected_doc_urls.update(discovered_doc_urls)

            if depth >= config.max_depth:
                continue

            for next_url in discovered_html_urls:
                if next_url not in visited_html_urls:
                    queue.append((next_url, depth + 1))

    if collected_doc_urls:
        docling_config = config.docling_config
        docling_config.category = config.category or docling_config.category
        docling_config.department = config.department or docling_config.department
        documents.extend(
            collect_documents_with_docling(
                sources=sorted(collected_doc_urls),
                config=docling_config,
            )
        )

    return documents


def _build_html_document(
    url: str,
    result,
    category: Optional[str],
    department: Optional[str],
    collected_at: datetime,
) -> Optional[Document]:
    markdown = getattr(result, "markdown", None)
    raw_markdown = getattr(markdown, "fit_markdown", None) or getattr(
        markdown, "raw_markdown", None
    )
    if not raw_markdown:
        return None

    content = raw_markdown.strip()
    if not content:
        return None

    title = _extract_title_from_crawl_result(result, content)
    if not title:
        return None

    return Document(
        doc_id=_build_doc_id(url),
        source_type="html",
        source_url=url,
        title=title,
        content=content,
        category=category,
        department=department,
        published_at=None,
        collected_at=collected_at,
    )


def _extract_links(
    base_url: str,
    result_links: Dict[str, List[Dict]],
    allowed_domains: Set[str],
    config: Crawl4AICollectorConfig,
) -> Tuple[Set[str], Set[str]]:
    html_urls: Set[str] = set()
    doc_urls: Set[str] = set()

    for link in result_links.get("internal", []):
        href = (link or {}).get("href")
        if not href:
            continue

        normalized = _normalize_url(urljoin(base_url, href))
        if not _is_allowed_url(normalized, allowed_domains, config):
            continue

        if _looks_like_document_url(normalized):
            doc_urls.add(normalized)
        else:
            html_urls.add(normalized)

    return html_urls, doc_urls


def _extract_title_from_crawl_result(result, content: str) -> Optional[str]:
    metadata = getattr(result, "metadata", None) or {}
    for key in ("title", "og:title"):
        value = metadata.get(key)
        if value:
            normalized = _normalize_text(value)
            if normalized and not _should_skip_title(normalized):
                return normalized[:300]

    for line in content.splitlines():
        normalized = _normalize_text(re.sub(r"^#+\s*", "", line))
        if not normalized or _should_skip_title(normalized):
            continue
        return normalized[:300]

    return None


def _looks_like_document_url(url: str) -> bool:
    lowered = url.lower()
    return any(ext in lowered for ext in DOCUMENT_EXTENSIONS)


def _is_allowed_url(
    url: str,
    allowed_domains: Set[str],
    config: Crawl4AICollectorConfig,
) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    domain = _normalize_domain(parsed.netloc)
    if allowed_domains and domain not in allowed_domains:
        return False

    lowered = url.lower()
    if any(pattern in lowered for pattern in config.exclude_patterns):
        return False

    if _looks_like_document_url(url):
        return True

    return any(pattern in lowered for pattern in config.include_patterns)


def _normalize_domain(domain: str) -> str:
    normalized = domain.lower().strip()
    if normalized.startswith("www."):
        return normalized[4:]
    return normalized


def _normalize_url(url: str) -> str:
    clean_url, _ = urldefrag(url)
    return clean_url.rstrip("/")


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _should_skip_title(value: str) -> bool:
    lowered = value.lower()
    skip_tokens = {"주메뉴", "닫기", "language", "login", "로그인", "검색"}
    return any(token in lowered for token in skip_tokens)


def _build_doc_id(source_url: str) -> str:
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
    return f"crawl-{digest}"
