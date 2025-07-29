from typing import List, Optional
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
    
    def get_document_types(self) -> List[str]:
        try:
            return self.rag_backend.get_document_types()
        except Exception as e:
            print(f"Error getting document types: {e}")
            return ["All"]
    
    def search_documents(self, query: str, client_filter: Optional[str] = None, document_type_filter: Optional[str] = None, top_k: int = 5, min_relevance: float = 0.0) -> SearchResult:
        try:
            answer, refs, latency, chunks = self.rag_backend.run_query_pipeline(
                query=query,
                client_filter=client_filter,
                document_type_filter=document_type_filter,
                top_k=top_k
            )
            
            snippets = []
            for i, chunk in enumerate(chunks):
                metadata = chunk.get("metadata", {})
                s3_path = metadata.get("s3_path", "")
                
                # Calculate relevance score
                relevance_score = 1.0 - chunk.get("distance", 0.0)
                
                # Filter by minimum relevance
                if relevance_score < min_relevance:
                    continue
                
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
                    relevance_score=relevance_score,
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
            # Log the error
            try:
                from ..utils.usage_logger import log_error
                log_error(
                    error_type="search_error",
                    error_message=str(e),
                    context={
                        "query": query[:100],  # Truncate long queries
                        "client_filter": client_filter,
                        "doc_type_filter": document_type_filter,
                        "top_k": top_k
                    }
                )
            except Exception:
                # Don't break if logging fails
                pass
            
            return SearchResult(
                query=query,
                summary=f"Error: {str(e)}",
                snippets=[],
                client_filter=client_filter,
                total_documents=0,
                processing_time=0.0
            )
