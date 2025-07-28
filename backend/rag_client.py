from typing import List, Optional
from .models import DocumentSnippet, SearchResult, PredefinedQuery
from .legal_rag import LegalRAGBackend

class RAGClient:
    def __init__(self):
        self.rag_backend = LegalRAGBackend()
    
    def get_predefined_queries(self) -> List[PredefinedQuery]:
        try:
            queries_data = self.rag_backend.get_predefined_queries()
            return [PredefinedQuery(**query) for query in queries_data]
        except Exception as e:
            print(f"Error getting predefined queries: {e}")
            return []
    
    def get_clients(self) -> List[str]:
        try:
            return self.rag_backend.get_clients()
        except Exception as e:
            print(f"Error getting clients: {e}")
            return ["All"]
    
    def search_documents(self, query: str, client_filter: Optional[str] = None) -> SearchResult:
        try:
            answer, refs, latency, chunks = self.rag_backend.run_query_pipeline(
                query=query,
                client_filter=client_filter,
                top_k=5
            )
            
            snippets = []
            for i, chunk in enumerate(chunks):
                metadata = chunk.get("metadata", {})
                s3_path = metadata.get("s3_path", "")
                
                presigned_url = None
                if s3_path:
                    presigned_url = self.rag_backend.generate_presigned_url(s3_path)
                
                if presigned_url:
                    metadata["presigned_url"] = presigned_url
                
                snippet = DocumentSnippet(
                    id=f"chunk_{i}",
                    title=metadata.get("file_name", "Unknown Document"),
                    content=metadata.get("text", ""),
                    source=metadata.get("client_account", "Unknown"),
                    relevance_score=1.0 - chunk.get("distance", 0.0),
                    distance=chunk.get("distance", 0.0),
                    section=metadata.get("document_type", "Unknown"),
                    metadata=metadata
                )
                snippets.append(snippet)
            
            return SearchResult(
                query=query,
                summary=answer or "No answer generated",
                snippets=snippets,
                client_filter=client_filter,
                total_documents=len(snippets),
                processing_time=latency / 1000.0
            )
            
        except Exception as e:
            return SearchResult(
                query=query,
                summary=f"Error: {str(e)}",
                snippets=[],
                client_filter=client_filter,
                total_documents=0,
                processing_time=0.0
            )
