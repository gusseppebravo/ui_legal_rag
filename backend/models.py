from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class DocumentSnippet:
    id: str
    title: str
    content: str
    source: str
    relevance_score: float
    distance: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SearchResult:
    query: str
    summary: str
    snippets: List[DocumentSnippet]
    client_filter: Optional[str] = None
    total_documents: int = 0
    processing_time: float = 0.0

@dataclass
class PredefinedQuery:
    id: str
    title: str
    description: str
    query_text: str
    category: str
