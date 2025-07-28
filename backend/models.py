"""
Data models for the legal document search application
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class DocumentSnippet:
    """Represents a document snippet returned by the RAG system"""
    id: str
    title: str
    content: str
    source: str
    relevance_score: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SearchResult:
    """Represents the complete search result"""
    query: str
    summary: str
    snippets: List[DocumentSnippet]
    client_filter: Optional[str] = None
    total_documents: int = 0
    processing_time: float = 0.0

@dataclass
class FullDocument:
    """Represents a complete document"""
    id: str
    title: str
    content: str
    client: str
    document_type: str
    date_created: datetime
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class PredefinedQuery:
    """Represents a predefined query option"""
    id: str
    title: str
    description: str
    query_text: str
    category: str
