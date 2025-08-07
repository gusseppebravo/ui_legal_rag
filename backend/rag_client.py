import json
from typing import List, Optional
import os
import pickle
import hashlib
from .models import DocumentSnippet, SearchResult, PredefinedQuery, MultiClientResult
from .legal_rag import LegalRAGBackend

class RAGClient:
    def __init__(self, use_cache: bool = True):
        self.rag_backend = LegalRAGBackend()
        self.use_cache = use_cache
        self.cache_dir = "cache"
        if self.use_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
        self.filter_values = self._load_filter_values()
    
    def _load_filter_values(self) -> dict:
        try:
            json_path = "unique_values_filter.json"
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading filter values: {e}")
            return {}
    
    def _get_cache_key(self, query: str, client_filter: str, document_type_filter: str, 
                      account_type_filter: str, solution_line_filter: str, related_product_filter: str, top_k: int) -> str:
        """Generate a cache key from search parameters"""
        cache_string = f"{query}|{client_filter}|{document_type_filter}|{account_type_filter}|{solution_line_filter}|{related_product_filter}|{top_k}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str):
        """Get cached result if it exists"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None
    
    def _save_to_cache(self, cache_key: str, result):
        """Save result to cache"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
        except Exception:
            pass  # Don't break if caching fails
    
    def _cached_search(self, query: str, client_filter: str, document_type_filter: str,
                      account_type_filter: str, solution_line_filter: str, related_product_filter: str, top_k: int):
        """Search with optional disk-based caching"""
        # If caching is disabled, directly call the backend
        if not self.use_cache:
            return self.rag_backend.run_query_pipeline(
                query=query,
                client_filter=client_filter if client_filter != "None" else None,
                document_type_filter=document_type_filter if document_type_filter != "None" else None,
                account_type_filter=account_type_filter if account_type_filter != "None" else None,
                solution_line_filter=solution_line_filter if solution_line_filter != "None" else None,
                related_product_filter=related_product_filter if related_product_filter != "None" else None,
                top_k=top_k
            )
        
        # Caching is enabled
        cache_key = self._get_cache_key(query, client_filter, document_type_filter, 
                                       account_type_filter, solution_line_filter, related_product_filter, top_k)
        
        # Try to get from cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # If not cached, perform the search
        result = self.rag_backend.run_query_pipeline(
            query=query,
            client_filter=client_filter if client_filter != "None" else None,
            document_type_filter=document_type_filter if document_type_filter != "None" else None,
            account_type_filter=account_type_filter if account_type_filter != "None" else None,
            solution_line_filter=solution_line_filter if solution_line_filter != "None" else None,
            related_product_filter=related_product_filter if related_product_filter != "None" else None,
            top_k=top_k
        )
        
        # Save to cache
        self._save_to_cache(cache_key, result)
        return result
    
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
            doc_types = self.filter_values.get("document_type", [])
            return ["All"] + doc_types
        except Exception as e:
            print(f"Error getting document types: {e}")
            return ["All"]
    
    def get_account_types(self) -> List[str]:
        try:
            account_types = self.filter_values.get("account_type", [])
            return ["All"] + account_types
            # return ["All"] + account_types
        except Exception as e:
            print(f"Error getting account types: {e}")
            return ["All", "Client", "Vendor"]

    def get_solution_lines(self) -> List[str]:
        try:
            solution_lines = self.filter_values.get("solution_line", [])
            return ["All"] + solution_lines
        except Exception as e:
            print(f"Error getting solution lines: {e}")
            return ["All"]

    def get_related_products(self) -> List[str]:
        try:
            related_products = self.filter_values.get("related_product", [])
            return ["All"] + related_products
        except Exception as e:
            print(f"Error getting related products: {e}")
            return ["All"]
    
    def search_documents(self, query: str, client_filter: Optional[str] = None, 
                        document_type_filter: Optional[str] = None, account_type_filter: Optional[str] = None,
                        solution_line_filter: Optional[str] = None, related_product_filter: Optional[str] = None,
                        top_k: int = 5, min_relevance: float = 0.0) -> SearchResult:
        try:
            # Use cached search with string keys for hashability
            cache_client = client_filter or "None"
            cache_doc_type = document_type_filter or "None"
            cache_account_type = account_type_filter or "None"
            cache_solution_line = solution_line_filter or "None"
            cache_related_product = related_product_filter or "None"
            
            answer, refs, latency, chunks = self._cached_search(query, cache_client, cache_doc_type, 
                                                              cache_account_type, cache_solution_line, cache_related_product, top_k)
            
            snippets = []
            for i, chunk in enumerate(chunks):
                metadata = chunk.get("metadata", {})
                
                s3_path = metadata.get("s3_path", "")
                
                # Extract file_name from s3_path if not directly available
                file_name = metadata.get("file_name")
                if not file_name and s3_path:
                    file_name = s3_path.split('/')[-1] if '/' in s3_path else s3_path
                
                # Handle new metadata structure: account_details[0] is client name, [2] is account type, [3] is related product
                client_account = "Unknown"
                account_details = metadata.get("account_details", [])
                if isinstance(account_details, list) and len(account_details) > 0:
                    client_account = account_details[0] if account_details[0] else "Unknown"
                else:
                    # Fallback to old structure if needed
                    client_account = metadata.get("client_account", "Unknown")
                    if isinstance(client_account, list):
                        client_account = client_account[0] if client_account else "Unknown"
                
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
                    title=file_name or "Unknown Document",
                    content=metadata.get("text", ""),
                    source=client_account,
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
    
    def search_multiple_clients(self, query: str, client_filters: List[str], document_type_filter: Optional[str] = None,
                               account_type_filter: Optional[str] = None, solution_line_filter: Optional[str] = None,
                               related_product_filter: Optional[str] = None, top_k: int = 5) -> MultiClientResult:
        import time
        start_time = time.time()
        
        client_results = {}
        client_search_results = {}
        
        for client in client_filters:
            if client == "All":
                continue
                
            try:
                # Use cached search for individual clients
                cache_doc_type = document_type_filter or "None"
                cache_account_type = account_type_filter or "None"
                cache_solution_line = solution_line_filter or "None"
                cache_related_product = related_product_filter or "None"
                
                answer, _, latency, chunks = self._cached_search(query, client, cache_doc_type,
                                                                cache_account_type, cache_solution_line, cache_related_product, top_k)
                client_results[client] = answer or "No answer found"
                
                # Store full search results for each client
                snippets = []
                for i, chunk in enumerate(chunks):
                    metadata = chunk.get("metadata", {})
                    
                    s3_path = metadata.get("s3_path", "")
                    
                    # Extract file_name from s3_path if not directly available
                    file_name = metadata.get("file_name")
                    if not file_name and s3_path:
                        file_name = s3_path.split('/')[-1] if '/' in s3_path else s3_path
                    
                    # Handle new metadata structure: account_details[0] is client name, [2] is account type, [3] is related product
                    client_account = "Unknown"
                    account_details = metadata.get("account_details", [])
                    if isinstance(account_details, list) and len(account_details) > 0:
                        client_account = account_details[0] if account_details[0] else "Unknown"
                    else:
                        # Fallback to old structure if needed
                        client_account = metadata.get("client_account", "Unknown")
                        if isinstance(client_account, list):
                            client_account = client_account[0] if client_account else "Unknown"
                    
                    relevance_score = 1.0 - chunk.get("distance", 0.0)
                    
                    presigned_url = None
                    if s3_path:
                        presigned_url = self.rag_backend.generate_presigned_url(s3_path)
                    if presigned_url:
                        metadata["presigned_url"] = presigned_url
                    
                    snippet = DocumentSnippet(
                        id=f"{client}_chunk_{i}",
                        title=file_name or "Unknown Document",
                        content=metadata.get("text", ""),
                        source=client_account,
                        relevance_score=relevance_score,
                        distance=chunk.get("distance", 0.0),
                        section=metadata.get("document_type", "Unknown"),
                        metadata=metadata
                    )
                    snippets.append(snippet)
                
                client_search_results[client] = SearchResult(
                    query=query,
                    summary=answer or "No answer generated",
                    snippets=snippets,
                    client_filter=client,
                    total_documents=len(snippets),
                    processing_time=latency / 1000.0
                )
                
            except Exception as e:
                client_results[client] = f"Error: {str(e)}"
                client_search_results[client] = SearchResult(
                    query=query,
                    summary=f"Error: {str(e)}",
                    snippets=[],
                    client_filter=client,
                    total_documents=0,
                    processing_time=0.0
                )
        
        tabular_summary = self._generate_tabular_summary(query, client_results)
        total_time = time.time() - start_time
        
        result = MultiClientResult(
            query=query,
            client_results=client_results,
            total_processing_time=total_time,
            tabular_summary=tabular_summary,
            client_search_results=client_search_results
        )
        
        return result
    
    def _generate_tabular_summary(self, query: str, client_results: dict) -> str:
        context = ""
        for client, answer in client_results.items():
            context += f"Client: {client}\nAnswer: {answer}\n\n"
        
        prompt = f"""Based on the following query and individual client responses, create a clean tabular summary.

Query: {query}

Individual Client Responses:
{context}

Create a markdown table with three columns: "Client", "Answer" and "Summary". 
In the Answer column directly answer the question, maybe Yes, No, Yes with limitation, etc.
In the Summary column keep summary concise but informative.
Focus on key findings, permissions, restrictions, or requirements for each client.

Only give the markdown table (do not include ```markdown ```, only give raw markdown). No comments."""

        try:
            response = self.rag_backend.azure_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a legal analyst. Create clear, concise tabular summaries of legal findings."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def get_accounts_by_type(self, account_type: str) -> List[str]:
        try:
            return self.rag_backend.get_accounts_by_type(account_type)
        except Exception as e:
            print(f"Error getting accounts by type: {e}")
            return []
