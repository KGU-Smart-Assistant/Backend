from pathlib import Path

from app.crawlers.parsing.parser_registry import load_registry


def test_load_registry_reads_yaml_templates() -> None:
    registry = load_registry(Path("app/crawlers/parsing/templates"))

    names = [entry["name"] for entry in registry]

    assert "kyonggi_notice_detail" in names
    assert "kyonggi_faq_list" in names
    assert "kyonggi_schedule" in names
    assert "generic_markdown" in names


def test_load_registry_normalizes_patterns_to_tuples() -> None:
    templates_dir = Path(".tmp/parser-registry-test")
    templates_dir.mkdir(parents=True, exist_ok=True)
    template_path = templates_dir / "custom.yaml"
    try:
        template_path.write_text(
            """
registry:
  - name: custom_notice
    url_patterns:
      - "notice"
    categories:
      - "notice"
    parser: notice_detail
""".strip(),
            encoding="utf-8",
        )

        registry = load_registry(templates_dir)

        assert registry == [
            {
                "name": "custom_notice",
                "url_patterns": ("notice",),
                "categories": ("notice",),
                "parser": "notice_detail",
            }
        ]
    finally:
        template_path.unlink(missing_ok=True)
        templates_dir.rmdir()
