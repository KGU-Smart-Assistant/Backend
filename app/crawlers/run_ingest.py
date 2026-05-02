import json
from pathlib import Path
import sys
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import yaml

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.crawlers import (
    chunk_documents,
    Crawl4AICollectorConfig,
    DoclingCollectorConfig,
    collect_documents_with_crawl4ai,
    select_latest_documents,
)

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


def embed_chunks(*args, **kwargs):
    from app.crawlers import embed_chunks as _embed_chunks

    return _embed_chunks(*args, **kwargs)


def load_sources_config(config_path: Path) -> List[Dict[str, Any]]:
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}
    sources = list(config.get("sources", []))
    sources.extend(
        _expand_generated_sources(
            department_sites=config.get("department_sites", []),
            source_blueprints=config.get("source_blueprints", []),
        )
    )
    return sources


def _expand_generated_sources(
    department_sites: List[Dict[str, Any]],
    source_blueprints: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    expanded_sources: List[Dict[str, Any]] = []

    for site in department_sites:
        slug = site.get("slug")
        base_url = site.get("base_url")
        site_type = site.get("site_type", "portal")
        source_overrides = site.get("source_overrides", {}) or {}
        if not slug or not base_url:
            continue

        for blueprint in source_blueprints:
            applies_to = blueprint.get("applies_to", ["portal"])
            if isinstance(applies_to, str):
                applies_to = [applies_to]
            if site_type not in applies_to:
                continue

            source = {
                key: value
                for key, value in blueprint.items()
                if key not in {"applies_to", "name_suffix", "seed_url_template"}
            }
            source["name"] = f"{slug}_{blueprint['name_suffix']}"
            source["department"] = site.get("department", slug)
            seed_url_template = blueprint.get("seed_url_template")
            if seed_url_template:
                source["seed_urls"] = [seed_url_template.format(base_url=base_url.rstrip("/"))]
            else:
                source["seed_urls"] = source.get("seed_urls") or [base_url]

            override = source_overrides.get(blueprint["name_suffix"], {})
            if override:
                source.update(override)
            expanded_sources.append(source)

    return expanded_sources


def build_crawler_config(source: Dict[str, Any]) -> Crawl4AICollectorConfig:
    seed_urls = source["seed_urls"]
    allowed_path_prefixes = source.get("allowed_path_prefixes")
    if allowed_path_prefixes is None:
        allowed_path_prefixes = _derive_allowed_path_prefixes(seed_urls)

    return Crawl4AICollectorConfig(
        seed_urls=seed_urls,
        max_pages=source.get("max_pages", 20),
        max_depth=source.get("max_depth", 2),
        max_pagination_pages=source.get("max_pagination_pages", 200),
        category=source.get("category"),
        department=source.get("department"),
        include_patterns=tuple(source.get("include_patterns", DEFAULT_INCLUDE_PATTERNS)),
        follow_patterns=(
            tuple(source["follow_patterns"]) if "follow_patterns" in source else None
        ),
        collect_patterns=(
            tuple(source["collect_patterns"]) if "collect_patterns" in source else None
        ),
        exclude_patterns=tuple(source.get("exclude_patterns", DEFAULT_EXCLUDE_PATTERNS)),
        allowed_path_prefixes=(
            tuple(allowed_path_prefixes) if allowed_path_prefixes is not None else None
        ),
        collect_seed_pages=source.get("collect_seed_pages", True),
        allowed_keyword_filters=(
            tuple(source["allowed_keyword_filters"])
            if "allowed_keyword_filters" in source
            else None
        ),
        blocked_keyword_filters=(
            tuple(source["blocked_keyword_filters"])
            if "blocked_keyword_filters" in source
            else None
        ),
        allowed_author_department_filters=(
            tuple(source["allowed_author_department_filters"])
            if "allowed_author_department_filters" in source
            else None
        ),
        blocked_author_department_filters=(
            tuple(source["blocked_author_department_filters"])
            if "blocked_author_department_filters" in source
            else None
        ),
        docling_config=DoclingCollectorConfig(
            category=source.get("category"),
            department=source.get("department"),
            skip_unsupported=source.get("skip_unsupported", False),
            skip_images=source.get("skip_images", False),
        ),
    )


def _derive_allowed_path_prefixes(seed_urls: List[str]) -> List[str]:
    prefixes: List[str] = []
    for seed_url in seed_urls:
        parsed = urlparse(seed_url)
        path = parsed.path or "/"
        if path == "/":
            prefix = "/"
        else:
            first_segment = path.strip("/").split("/", 1)[0]
            prefix = f"/{first_segment}/" if first_segment else "/"
        if prefix not in prefixes:
            prefixes.append(prefix)
    return prefixes


def default_report_output_dir() -> Path:
    return PROJECT_ROOT / ".tmp" / "ingest-reports"


def write_ingest_report(report: Dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = output_dir / f"ingest-report-{timestamp}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_path


def classify_source_report(
    *,
    category: str | None,
    raw_documents: int,
    documents: int,
    exact_duplicates_removed: int,
    version_duplicates_removed: int,
) -> Dict[str, str]:
    if raw_documents == 0:
        return {
            "status": "no_content_discovered",
            "reason": "No crawlable documents were discovered from the source.",
        }

    if documents == 0:
        if exact_duplicates_removed or version_duplicates_removed:
            return {
                "status": "fully_deduplicated",
                "reason": "Documents were discovered but removed as duplicates or older versions.",
            }
        if category == "faq":
            return {
                "status": "empty_board_or_filtered",
                "reason": "FAQ board was empty or filtered out as a non-detail page.",
            }
        return {
            "status": "filtered_out_or_empty",
            "reason": "Documents were discovered but filtered out or reduced to zero usable items.",
        }

    return {
        "status": "ok",
        "reason": "Source produced usable documents.",
    }


def main() -> None:
    config_path = Path(__file__).resolve().with_name("sources.yaml")

    sources = load_sources_config(config_path)
    if not sources:
        print("No sources configured in app/crawlers/sources.yaml")
        return

    total_documents = 0
    total_chunks = 0
    total_embedded_chunks = 0
    source_reports: List[Dict[str, Any]] = []
    source_status_counts: Dict[str, int] = {}

    for source in sources:
        crawler_config = build_crawler_config(source)
        raw_documents = collect_documents_with_crawl4ai(crawler_config)
        dedup_result = select_latest_documents(raw_documents)
        documents = dedup_result.documents
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

        source_summary = classify_source_report(
            category=source.get("category"),
            raw_documents=dedup_result.total_input,
            documents=len(documents),
            exact_duplicates_removed=dedup_result.exact_duplicates_removed,
            version_duplicates_removed=dedup_result.version_duplicates_removed,
        )
        source_status_counts[source_summary["status"]] = (
            source_status_counts.get(source_summary["status"], 0) + 1
        )
        source_reports.append(
            {
                "name": source["name"],
                "category": source.get("category"),
                "department": source.get("department"),
                "seed_urls": source["seed_urls"],
                "raw_documents": dedup_result.total_input,
                "documents": len(documents),
                "exact_duplicates_removed": dedup_result.exact_duplicates_removed,
                "version_duplicates_removed": dedup_result.version_duplicates_removed,
                "chunks": len(chunks),
                "embedded_chunks": embedded_count,
                "status": source_summary["status"],
                "status_reason": source_summary["reason"],
            }
        )

        print(
            f"[{source['name']}] raw_documents={dedup_result.total_input} "
            f"documents={len(documents)} "
            f"exact_duplicates_removed={dedup_result.exact_duplicates_removed} "
            f"version_duplicates_removed={dedup_result.version_duplicates_removed} "
            f"chunks={len(chunks)} embedded_chunks={embedded_count} "
            f"status={source_summary['status']}"
        )

    print(f"total_documents={total_documents}")
    print(f"total_chunks={total_chunks}")
    print(f"total_embedded_chunks={total_embedded_chunks}")

    report = {
        "generated_at": datetime.now().isoformat(),
        "source_count": len(sources),
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "total_embedded_chunks": total_embedded_chunks,
        "source_status_counts": source_status_counts,
        "sources": source_reports,
    }
    report_path = write_ingest_report(report, default_report_output_dir())
    print(f"ingest_report={report_path}")


if __name__ == "__main__":
    main()
