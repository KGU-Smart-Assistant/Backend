from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class ParseContext:
    url: str
    category: Optional[str]
    department: Optional[str]
    allowed_keyword_filters: Optional[Tuple[str, ...]] = None
    blocked_keyword_filters: Optional[Tuple[str, ...]] = None


@dataclass
class ParsedDocument:
    title: str
    content: str
    published_at: Optional[datetime] = None
    author_department: Optional[str] = None
    attachment_urls: List[str] = field(default_factory=list)
