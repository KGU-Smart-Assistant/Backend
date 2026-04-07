import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.schemas import Document


@dataclass
class NoticeCrawlerConfig:
    list_url: str
    list_item_selector: str
    detail_link_selector: str
    title_selector: str
    content_selector: str
    published_at_selector: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    source_type: str = "notice"
    timeout_seconds: int = 10


def crawl_notice_documents(
    config: NoticeCrawlerConfig,
    limit: int = 10,
) -> List[Document]:
    """Crawl a notice board and return normalized documents."""
    list_html = _fetch_html(config.list_url, timeout_seconds=config.timeout_seconds)
    detail_urls = _extract_detail_urls(list_html=list_html, config=config, limit=limit)

    documents: List[Document] = []
    collected_at = datetime.now()

    for detail_url in detail_urls:
        detail_html = _fetch_html(detail_url, timeout_seconds=config.timeout_seconds)
        document = _parse_notice_document(
            detail_html=detail_html,
            detail_url=detail_url,
            config=config,
            collected_at=collected_at,
        )
        documents.append(document)

    return documents


def _fetch_html(url: str, timeout_seconds: int) -> str:
    response = requests.get(
        url,
        timeout=timeout_seconds,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.text


def _extract_detail_urls(
    list_html: str,
    config: NoticeCrawlerConfig,
    limit: int,
) -> List[str]:
    soup = BeautifulSoup(list_html, "html.parser")
    detail_urls: List[str] = []

    for item in soup.select(config.list_item_selector):
        link = item.select_one(config.detail_link_selector)
        if link is None:
            continue

        href = link.get("href")
        if not href:
            continue

        detail_urls.append(urljoin(config.list_url, href))
        if len(detail_urls) >= limit:
            break

    return detail_urls


def _parse_notice_document(
    detail_html: str,
    detail_url: str,
    config: NoticeCrawlerConfig,
    collected_at: datetime,
) -> Document:
    soup = BeautifulSoup(detail_html, "html.parser")

    title = _extract_text(soup, config.title_selector)
    content = _extract_text(soup, config.content_selector)
    published_at = _extract_published_at(soup, config.published_at_selector)

    return Document(
        doc_id=_build_doc_id(detail_url),
        source_type=config.source_type,
        source_url=detail_url,
        title=title,
        content=content,
        category=config.category,
        department=config.department,
        published_at=published_at,
        collected_at=collected_at,
    )


def _extract_text(soup: BeautifulSoup, selector: str) -> str:
    node = soup.select_one(selector)
    if node is None:
        raise ValueError(f"Required selector not found: {selector}")

    text = node.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        raise ValueError(f"Empty text extracted from selector: {selector}")

    return text


def _extract_published_at(
    soup: BeautifulSoup,
    selector: Optional[str],
) -> Optional[datetime]:
    if not selector:
        return None

    node = soup.select_one(selector)
    if node is None:
        return None

    raw_text = node.get_text(" ", strip=True)
    if not raw_text:
        return None

    match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", raw_text)
    if not match:
        return None

    year, month, day = match.groups()
    return datetime(int(year), int(month), int(day))


def _build_doc_id(source_url: str) -> str:
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:12]
    return f"notice-{digest}"
