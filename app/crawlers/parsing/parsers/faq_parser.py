from app.crawlers.parsing.parsers.base import BaseParser
from app.crawlers.parsing.schemas import ParseContext, ParsedDocument


class FaqParser(BaseParser):
    def parse(self, result, context: ParseContext) -> ParsedDocument | None:
        markdown = getattr(result, "markdown", None)
        raw_markdown = getattr(markdown, "fit_markdown", None) or getattr(
            markdown, "raw_markdown", None
        )
        if not raw_markdown:
            return None

        content = raw_markdown.strip()
        if not content:
            return None

        normalized = " ".join(content.split())
        if "총게시물 : 0" in normalized or "총게시물: 0" in normalized:
            return None
        if "selectbbsnttlist.do" in context.url.lower():
            return None

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("![") or stripped.startswith("["):
                continue
            return ParsedDocument(title=stripped[:300], content=content)

        return None
