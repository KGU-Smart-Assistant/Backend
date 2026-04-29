import asyncio
import hashlib
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urldefrag, urljoin, urlparse, urlunparse

from app.crawlers.docling_collector import (
    DoclingCollectorConfig,
    collect_documents_with_docling,
)
from app.crawlers.parsing.parser_router import ParserRouter
from app.crawlers.parsing.schemas import ParseContext
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
    "search.do",
    "javascript:",
    "mailto:",
)

PARSER_ROUTER = ParserRouter()


@dataclass
class Crawl4AICollectorConfig:
    seed_urls: List[str]
    max_pages: int = 20
    max_depth: int = 2
    category: Optional[str] = None
    department: Optional[str] = None
    include_patterns: Tuple[str, ...] = DEFAULT_INCLUDE_PATTERNS
    follow_patterns: Optional[Tuple[str, ...]] = None
    collect_patterns: Optional[Tuple[str, ...]] = None
    exclude_patterns: Tuple[str, ...] = DEFAULT_EXCLUDE_PATTERNS
    allowed_domains: Optional[Set[str]] = None
    headless: bool = True
    word_count_threshold: int = 1
    page_timeout_ms: int = 30000
    collect_seed_pages: bool = True
    allowed_keyword_filters: Optional[Tuple[str, ...]] = None
    blocked_keyword_filters: Optional[Tuple[str, ...]] = None
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

    queue: Deque[Tuple[str, int]] = deque((_normalize_url(url), 0) for url in config.seed_urls)
    visited_html_urls: Set[str] = set()
    collected_doc_urls: Set[str] = set()
    documents: List[Document] = []
    collected_at = datetime.now()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and len(visited_html_urls) < config.max_pages:
            current_url, depth = queue.popleft()
            if current_url in visited_html_urls:
                continue
            if depth != 0 and not _is_allowed_url(current_url, allowed_domains, config):
                continue

            result = await crawler.arun(url=current_url, config=run_config)
            visited_html_urls.add(current_url)

            if not getattr(result, "success", False):
                continue

            if _should_collect_html_url(
                url=current_url,
                config=config,
                is_seed=depth == 0,
            ):
                html_document = _build_html_document(
                    url=current_url,
                    result=result,
                    category=config.category,
                    department=config.department,
                    collected_at=collected_at,
                    allowed_keyword_filters=config.allowed_keyword_filters,
                    blocked_keyword_filters=config.blocked_keyword_filters,
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

            for next_url in sorted(discovered_html_urls, key=_html_url_priority):
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
    allowed_keyword_filters: Optional[Tuple[str, ...]] = None,
    blocked_keyword_filters: Optional[Tuple[str, ...]] = None,
) -> Optional[Document]:
    parsed = PARSER_ROUTER.parse(
        result=result,
        context=ParseContext(
            url=url,
            category=category,
            department=department,
            allowed_keyword_filters=allowed_keyword_filters,
            blocked_keyword_filters=blocked_keyword_filters,
        ),
    )
    if parsed is None:
        return None

    return Document(
        doc_id=_build_doc_id(url),
        source_type="html",
        source_url=url,
        title=parsed.title,
        content=parsed.content,
        category=category,
        department=department,
        author_department=parsed.author_department,
        published_at=parsed.published_at,
        attachment_urls=parsed.attachment_urls,
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


def _looks_like_document_url(url: str) -> bool:
    lowered = url.lower()
    return any(ext in lowered for ext in DOCUMENT_EXTENSIONS)


def _should_collect_html_url(
    url: str,
    config: Crawl4AICollectorConfig,
    is_seed: bool,
) -> bool:
    if is_seed and not config.collect_seed_pages:
        return False

    patterns = config.collect_patterns or config.include_patterns
    if not patterns:
        return True

    lowered = url.lower()
    return any(pattern in lowered for pattern in patterns)


def _html_url_priority(url: str) -> Tuple[int, str]:
    lowered = url.lower()
    if "selectbbsnttview.do" in lowered:
        return (0, lowered)
    if "selectbbsnttlist.do" in lowered:
        return (1, lowered)
    if "contents.do" in lowered:
        return (2, lowered)
    return (3, lowered)


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

    patterns = config.follow_patterns or config.include_patterns
    if not patterns:
        return True

    return any(pattern in lowered for pattern in patterns)


def _normalize_domain(domain: str) -> str:
    normalized = domain.lower().strip()
    if normalized.startswith("www."):
        return normalized[4:]
    return normalized


def _normalize_url(url: str) -> str:
    clean_url, _ = urldefrag(url)
    parsed = urlparse(clean_url)
    normalized_params = ""
    if parsed.params and not re.fullmatch(r"jsessionid=[^/?#]+", parsed.params, flags=re.IGNORECASE):
        normalized_params = parsed.params
    normalized_query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    rebuilt = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            normalized_params,
            normalized_query,
            parsed.fragment,
        )
    )
    return rebuilt.rstrip("/")


def _build_doc_id(source_url: str) -> str:
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
    return f"crawl-{digest}"
