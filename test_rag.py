#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/legal-RAG-pipeline/ui_legal_rag')

from backend.legal_rag import LegalRAGBackend

def test_rag():
    backend = LegalRAGBackend()
    
    print("Testing Legal RAG Backend...")
    
    clients = backend.get_clients()
    print(f"Clients loaded: {len(clients)}")
    
    queries = backend.get_predefined_queries()
    print(f"Predefined queries: {len(queries)}")
    
    test_query = "Can we use client data to develop new services?"
    print(f"Testing query: {test_query}")
    
    answer, refs, latency, chunks = backend.run_query_pipeline(test_query, top_k=3)
    
    print(f"Response time: {latency}ms")
    print(f"Chunks retrieved: {len(chunks)}")
    print(f"Answer: {answer[:100]}...")
    
    if chunks:
        sample_chunk = chunks[0]
        metadata = sample_chunk.get('metadata', {})
        s3_path = metadata.get('s3_path')
        if s3_path:
            presigned_url = backend.generate_presigned_url(s3_path)
            print(f"PDF access: {'✓' if presigned_url else '✗'}")
    
    print("✓ RAG backend test complete")

if __name__ == "__main__":
    test_rag()
