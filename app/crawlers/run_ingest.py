from pathlib import Path
import sys
from typing import Any, Dict, List

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.crawlers import (
    Crawl4AICollectorConfig,
    DoclingCollectorConfig,
    collect_documents_with_crawl4ai,
)
from app.services import chunk_documents, embed_chunks

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


def load_sources_config(config_path: Path) -> List[Dict[str, Any]]:
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}
    return config.get("sources", [])


def build_crawler_config(source: Dict[str, Any]) -> Crawl4AICollectorConfig:
    return Crawl4AICollectorConfig(
        seed_urls=source["seed_urls"],
        max_pages=source.get("max_pages", 20),
        max_depth=source.get("max_depth", 2),
        category=source.get("category"),
        department=source.get("department"),
        include_patterns=tuple(source.get("include_patterns", DEFAULT_INCLUDE_PATTERNS)),
        exclude_patterns=tuple(source.get("exclude_patterns", DEFAULT_EXCLUDE_PATTERNS)),
        docling_config=DoclingCollectorConfig(
            category=source.get("category"),
            department=source.get("department"),
            skip_unsupported=source.get("skip_unsupported", False),
        ),
    )


def main() -> None:
    config_path = Path(__file__).resolve().with_name("sources.yaml")

    sources = load_sources_config(config_path)
    if not sources:
        print("No sources configured in app/crawlers/sources.yaml")
        return

    total_documents = 0
    total_chunks = 0
    total_embedded_chunks = 0

    for source in sources:
        crawler_config = build_crawler_config(source)
        documents = collect_documents_with_crawl4ai(crawler_config)
        chunks = chunk_documents(documents, chunk_size=1000, chunk_overlap=200)
        embedded_count = 0

        if source.get("embed", True) and chunks:
            embedding_limit = source.get("embedding_limit")
            target_chunks = chunks[:embedding_limit] if embedding_limit else chunks
            embedded_chunks = embed_chunks(target_chunks)
            embedded_count = len(embedded_chunks)
            total_embedded_chunks += embedded_count

        total_documents += len(documents)
        total_chunks += len(chunks)

        print(
            f"[{source['name']}] documents={len(documents)} "
            f"chunks={len(chunks)} embedded_chunks={embedded_count}"
        )

    print(f"total_documents={total_documents}")
    print(f"total_chunks={total_chunks}")
    print(f"total_embedded_chunks={total_embedded_chunks}")


if __name__ == "__main__":
    main()
