import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

from app.schemas import Document

HWP_EXTENSIONS = {".hwp", ".hwpx"}


@dataclass
class DoclingCollectorConfig:
    category: Optional[str] = None
    department: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    skip_unsupported: bool = False


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
            result = converter.convert(source, headers=config.headers or None)
        except ValueError:
            if config.skip_unsupported:
                continue
            raise

        content = result.document.export_to_markdown().strip()
        if not content:
            continue

        documents.append(
            Document(
                doc_id=_build_doc_id(source),
                source_type=_infer_source_type(source),
                source_url=source,
                title=_extract_title(content=content, source=source),
                content=content,
                category=config.category,
                department=config.department,
                published_at=None,
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


def _infer_source_type(source: str) -> str:
    suffix = Path(urlparse(source).path).suffix.lower()

    if suffix == ".pdf":
        return "pdf"
    if suffix == ".docx":
        return "docx"
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}:
        return "image"
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    return "file"


def _extract_title(content: str, source: str) -> str:
    for line in content.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        if normalized.startswith("#"):
            title = re.sub(r"^#+\s*", "", normalized).strip()
            if title:
                return title[:300]
        return normalized[:300]

    fallback = Path(urlparse(source).path).stem or source
    return fallback[:300]


def _build_doc_id(source: str) -> str:
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"doc-{digest}"
