#!/usr/bin/env python3

import sys
import os
import requests
import json

from backend.legal_rag import LegalRAGBackend

def test_embedding_api():
    """Test the embedding API directly to debug the response"""
    print("=== TESTING EMBEDDING API DIRECTLY ===")
    
    API_KEY = "2jIpWCyNRg3Y8lkbmWG0tkyXwYlJn5QaZ1F3yKf7"
    EMBEDDINGS_URL = "https://zgggzg2iqg.execute-api.us-east-1.amazonaws.com/dev/get_embeddings"
    
    payload = {
        "model_name": "e5_mistral_embed_384",
        "texts": ["Can we use client data to develop new services?"]
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Making request to: {EMBEDDINGS_URL}")
        print(f"Payload: {payload}")
        
        response = requests.post(EMBEDDINGS_URL, json=payload, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"Raw response keys: {list(response_json.keys())}")
            print(f"Raw response: {response_json}")
            
            # Try parsing the body
            if 'body' in response_json:
                raw_body = response_json.get('body')
                print(f"Raw body type: {type(raw_body)}")
                print(f"Raw body: {raw_body}")
                
                if raw_body:
                    try:
                        parsed_body = json.loads(raw_body)
                        print(f"Parsed body: {parsed_body}")
                        print(f"Embeddings key exists: {'embeddings' in parsed_body}")
                        if 'embeddings' in parsed_body:
                            embeddings = parsed_body['embeddings']
                            print(f"Embeddings type: {type(embeddings)}")
                            print(f"Embeddings length: {len(embeddings) if embeddings else 'None'}")
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse body as JSON: {e}")
                else:
                    print("Body is None or empty")
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Exception during API call: {e}")

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
    # Test the embedding API first
    # test_embedding_api()
    # print("\n" + "="*50 + "\n")
    # Then test the full RAG pipeline
    test_rag()
