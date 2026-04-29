import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.schemas import Document

HWP_EXTENSIONS = {".hwp", ".hwpx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
HTML_EXTENSIONS = {".html", ".htm"}
MARKDOWN_EXTENSIONS = {".md", ".markdown"}


@dataclass
class DoclingCollectorConfig:
    category: Optional[str] = None
    department: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    skip_unsupported: bool = False
    skip_images: bool = False
    timeout_seconds: int = 10


def collect_documents_with_docling(
    sources: Iterable[str],
    config: Optional[DoclingCollectorConfig] = None,
) -> List[Document]:
    """Convert file paths or URLs into normalized documents using Docling."""
    config = config or DoclingCollectorConfig()
    converter = _create_converter()
    collected_at = datetime.now()
    documents: List[Document] = []

    for source in sources:
        try:
            _validate_supported_source(source)
            source_type = _infer_source_type(
                source=source,
                headers=config.headers,
                timeout_seconds=config.timeout_seconds,
            )
            if source_type == "image" and config.skip_images:
                continue
            result = converter.convert(source, headers=config.headers or None)
        except ValueError:
            if config.skip_unsupported:
                continue
            raise

        content = result.document.export_to_markdown().strip()
        if not content:
            continue

        title = _extract_title(
            content=content,
            source=source,
            source_type=source_type,
            headers=config.headers,
            timeout_seconds=config.timeout_seconds,
        )

        documents.append(
            Document(
                doc_id=_build_doc_id(source),
                source_type=source_type,
                source_url=source,
                title=title,
                content=content,
                category=config.category,
                department=config.department,
                author_department=config.department,
                published_at=None,
                attachment_urls=[],
                collected_at=collected_at,
            )
        )

    return documents


def _create_converter():
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError(
            "Docling is not installed. Add 'docling' to dependencies and install it first."
        ) from exc

    return DocumentConverter()


def _validate_supported_source(source: str) -> None:
    suffix = Path(urlparse(source).path).suffix.lower()
    if suffix in HWP_EXTENSIONS:
        raise ValueError(
            "Docling does not officially support HWP/HWPX. "
            "Convert HWP/HWPX to PDF or DOCX before ingestion."
        )


def _infer_source_type(
    source: str,
    headers: Dict[str, str],
    timeout_seconds: int,
) -> str:
    lowered_source = source.lower()
    if ".pdf" in lowered_source:
        return "pdf"
    if ".docx" in lowered_source:
        return "docx"

    suffix = Path(urlparse(source).path).suffix.lower()

    if suffix == ".pdf":
        return "pdf"
    if suffix == ".docx":
        return "docx"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in HTML_EXTENSIONS:
        return "html"
    if suffix in MARKDOWN_EXTENSIONS:
        return "markdown"

    content_type = _detect_content_type(
        source=source,
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    if not content_type:
        if _is_url(source):
            return "html"
        return "file"

    normalized = content_type.lower()
    if "pdf" in normalized:
        return "pdf"
    if "wordprocessingml.document" in normalized or "msword" in normalized:
        return "docx"
    if normalized.startswith("image/"):
        return "image"
    if "html" in normalized:
        return "html"
    if "markdown" in normalized or "text/plain" in normalized:
        return "markdown"

    return "file"


def _extract_title(
    content: str,
    source: str,
    source_type: str,
    headers: Dict[str, str],
    timeout_seconds: int,
) -> str:
    if source_type == "html":
        html_title = _extract_html_title(
            source=source,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        if html_title:
            return html_title[:300]

    for line in content.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        plain_text = re.sub(r"^#+\s*", "", normalized).strip()
        if plain_text and _should_skip_title_candidate(plain_text):
            continue
        if normalized.startswith("#"):
            title = plain_text
            if title:
                return title[:300]
        return normalized[:300]

    fallback = Path(urlparse(source).path).stem or source
    return fallback[:300]


def _extract_html_title(
    source: str,
    headers: Dict[str, str],
    timeout_seconds: int,
) -> Optional[str]:
    try:
        if _is_url(source):
            response = requests.get(
                source,
                timeout=timeout_seconds,
                headers=headers or None,
            )
            response.raise_for_status()
            html = response.text
        else:
            html = Path(source).read_text(encoding="utf-8")
    except Exception:
        return None

    soup = BeautifulSoup(html, "html.parser")

    og_title = soup.select_one('meta[property="og:title"]')
    if og_title and og_title.get("content"):
        normalized = _normalize_title_text(og_title["content"])
        if normalized and not _looks_like_navigation_text(normalized):
            return normalized

    if soup.title and soup.title.string:
        normalized = _normalize_title_text(soup.title.string)
        if normalized and not _looks_like_navigation_text(normalized):
            return normalized

    first_heading = soup.select_one("h1")
    if first_heading:
        normalized = _normalize_title_text(first_heading.get_text(" ", strip=True))
        if normalized and not _looks_like_navigation_text(normalized):
            return normalized

    return None


def _normalize_title_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _looks_like_navigation_text(value: str) -> bool:
    lowered = value.lower()
    navigation_tokens = {"주메뉴", "메뉴", "home", "login", "사이트맵", "검색"}
    return any(token in lowered for token in navigation_tokens)


def _should_skip_title_candidate(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return True
    if _looks_like_navigation_text(normalized):
        return True
    if normalized.startswith(("- [", "* [")):
        return True
    if re.fullmatch(r"\[.+\]\(.+\)", normalized):
        return True
    if re.fullmatch(r"-\s*\[.+\]\(.+\)", normalized):
        return True
    return False


def _detect_content_type(
    source: str,
    headers: Dict[str, str],
    timeout_seconds: int,
) -> Optional[str]:
    if not _is_url(source):
        return None

    request_headers = headers or None

    try:
        response = requests.head(
            source,
            timeout=timeout_seconds,
            headers=request_headers,
            allow_redirects=True,
        )
        content_type = response.headers.get("Content-Type")
        if content_type:
            return content_type
    except Exception:
        pass

    try:
        response = requests.get(
            source,
            timeout=timeout_seconds,
            headers=request_headers,
            stream=True,
        )
        content_type = response.headers.get("Content-Type")
        response.close()
        return content_type
    except Exception:
        return None


def _is_url(source: str) -> bool:
    parsed = urlparse(source)
    return parsed.scheme in {"http", "https"}


def _build_doc_id(source: str) -> str:
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"doc-{digest}"
