#!/usr/bin/env python3

import sys
import os


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
    
    # Test without filters first to get raw chunks
    print("\n=== TESTING WITHOUT FILTERS ===")
    answer, refs, latency, chunks = backend.run_query_pipeline(test_query, top_k=3)
    
    print(f"Response time: {latency}ms")
    print(f"Chunks retrieved: {len(chunks)}")
    
    # Debug chunk metadata
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n=== DEBUG CHUNK {i} ===")
        print(f"Chunk keys: {list(chunk.keys())}")
        
        metadata = chunk.get('metadata', {})
        print(f"Metadata keys: {list(metadata.keys())}")
        
        # Show sample metadata (truncate long values)
        sample_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > 100:
                sample_metadata[key] = value[:100] + "..."
            else:
                sample_metadata[key] = value
        
        print(f"Metadata sample: {sample_metadata}")
    
    print(f"\nAnswer preview: {answer[:100] if answer else 'No answer'}...")
    
    # Test with filters to see what breaks
    print("\n=== TESTING WITH FILTERS ===")
    try:
        answer2, refs2, latency2, chunks2 = backend.run_query_pipeline(
            test_query, 
            account_type_filter="Client",
            top_k=3
        )
        print(f"Filter test successful: {len(chunks2)} chunks")
    except Exception as e:
        print(f"Filter test failed: {e}")
    
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
