import io
import os
import json
import boto3
import requests
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from openai import AzureOpenAI
import time

API_KEY = "2jIpWCyNRg3Y8lkbmWG0tkyXwYlJn5QaZ1F3yKf7"
S3_BUCKET = "ml-legal-restricted"
VECTOR_BUCKET_NAME = "legal-docs-vector-store"
EMBEDDINGS_URL = "https://zgggzg2iqg.execute-api.us-east-1.amazonaws.com/dev/get_embeddings"
# INDEX_NAME = 'token-chunking-poc'
INDEX_NAME = 'token-chunking-metadata-enriched'

AZURE_OPENAI_ENDPOINT = "https://ironclad-openai-001.openai.azure.com/"
AZURE_OPENAI_API_KEY = "936856630b764210913d9a8fd6c8212b"
AZURE_DEPLOYMENT_NAME = "gpt-4o"

class LegalRAGBackend:
    
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.s3v = boto3.client("s3vectors", region_name="us-east-1")
        self.azure_client = self._load_azure_client()
        self.clients_data = self._load_clients_data()
        
    def _load_azure_client(self) -> AzureOpenAI:
        return AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2023-05-15",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
    
    def _load_clients_data(self) -> List[str]:
        try:
            csv_path = "files_per_client_summary.csv"
            df = pd.read_csv(csv_path)
            clients = ["All"] + df['client_account'].tolist()
            return clients
        except Exception as e:
            print(f"Error loading clients data: {e}")
            return ["All"]
    
    def get_text_embedding(self, texts, model='e5_mistral_embed_384'):
        if isinstance(texts, str):
            texts = [texts]
            
        if not isinstance(texts, list) or not texts:
            raise ValueError("Input 'texts' must be a non-empty list of strings.")

        embeddings = []

        for text in texts:
            if not isinstance(text, str):
                raise ValueError("Each item in 'texts' must be a string.")

            payload = {
                "model_name": model,
                "texts": [text]
            }

            headers = {
                "x-api-key": API_KEY
            }

            try:
                response = requests.post(EMBEDDINGS_URL, json=payload, headers=headers)
                response.raise_for_status()

                raw_body = response.json().get('body')
                parsed_body = json.loads(raw_body)
                embedding = parsed_body.get('embeddings')
                
                if not embedding or not isinstance(embedding, list) or len(embedding) != 1:
                    raise KeyError(f"No valid embedding found in response for text: '{text}'")

                embedding_float32 = np.array(embedding[0], dtype=np.float32).tolist()
                embeddings.append(embedding_float32)
                
            except Exception as e:
                print(f"[ERROR] Failed to get embedding for text: {e}")
                embeddings.append(None)

        return embeddings[0] if len(embeddings) == 1 else embeddings

    def query_s3_vector_store(self, query_text: str, client_account_filter: Optional[str] = None, 
                               document_type_filter: Optional[str] = None, top_k: int = 5):
        query_embedding = self.get_text_embedding(query_text)
        filter_expression = {}
        
        # Build filter expression with multiple conditions
        if client_account_filter and client_account_filter != "All":
            filter_expression["client_account_details"] = {"$in": [client_account_filter]}
            
        if document_type_filter and document_type_filter != "All":
            filter_expression["document_type"] = {"$eq": document_type_filter}

        # Only apply filter if we have conditions
        final_filter = filter_expression if filter_expression else None

        try:
            response = self.s3v.query_vectors(
                vectorBucketName=VECTOR_BUCKET_NAME,
                indexName=INDEX_NAME,
                topK=top_k,
                queryVector={
                    'float32': query_embedding
                },
                returnMetadata=True,
                returnDistance=True,
                filter=final_filter
            )
            
            return response
        except Exception as e:
            print(f"❌ Error querying S3 Vector Store: {e}")
            return None

    def build_prompt(self, query: str, top_chunks: Dict[str, Any]):
        context = ""
        source_refs = {}
        chunks = top_chunks.get('vectors', [])
        
        for i, chunk in enumerate(chunks):
            ref = f"[{i+1}]"
            metadata = chunk.get("metadata", {})
            source = metadata.get("s3_path", "unknown")
            chunk_text = metadata.get("text", "")
            
            context += f"{ref} ({source}):\n{chunk_text}\n\n"
            source_refs[ref] = metadata

        prompt = f"""You are a legal document analyst. Analyze the following context to provide a comprehensive answer to the question.

Focus on:
- What the documents DO say (positive findings)
- Specific requirements, permissions, or restrictions
- Actionable information and clear guidance
- Direct quotes and specific clauses when relevant

If information is not explicitly stated, indicate what is missing rather than just saying "does not mention."

Context:
{context}

Question: {query}

Answer:"""
        return prompt, source_refs

    def run_query_pipeline(self, query: str, client_filter: Optional[str] = None, 
                          document_type_filter: Optional[str] = None, top_k: int = 5):
        print(f"\n🔍 Running RAG query for: {query}\n")
        start = time.time()

        chunks = self.query_s3_vector_store(query, client_filter, document_type_filter, top_k=top_k)

        if not chunks:
            print("❗ No chunks returned from vector store.")
            return None, {}, 0, []

        print(f"✅ Chunks response received: {type(chunks)}")
        print(f"Chunks keys: {list(chunks.keys()) if chunks else 'None'}")
        
        vectors = chunks.get('vectors', [])
        print(f"Number of vectors in chunks: {len(vectors)}")
        
        if not vectors:
            print("❌ No vectors in chunks response!")
            return None, {}, 0, []

        prompt, refs = self.build_prompt(query, chunks)
        print(f"Context length: {len(prompt)}")

        response = self.azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal document analyst. Provide comprehensive, actionable answers based on the context provided. "
                               "Focus on what documents DO say rather than what they don't mention. "
                               "Cite sources using [1], [2], etc. based on the exact chunks provided. "
                               "When information is incomplete, explain what specific details are missing."
                },
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content.strip()
        latency = round((time.time() - start) * 1000, 2)

        return answer, refs, latency, chunks.get('vectors', [])

    def generate_presigned_url(self, s3_path: str, expiration: int = 3600) -> Optional[str]:
        try:
            if s3_path.startswith('s3://'):
                s3_path = s3_path[5:]
            
            parts = s3_path.split('/', 1)
            if len(parts) != 2:
                print(f"Invalid S3 path format: {s3_path}")
                return None
            
            bucket_name, object_key = parts
            
            presigned_url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except Exception as e:
            print(f"Error generating presigned URL for {s3_path}: {e}")
            return None

    def get_clients(self) -> List[str]:
        return self.clients_data

    def get_document_types(self) -> List[str]:
        return ["All", "Contract", "Amendment", "Addendum", "SOW", "MSA", "Agreement", "Policy"]

    def get_predefined_queries(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "1",
                "title": "Can we use client data to develop or test new services?",
                "description": "Search for terms regarding use of client data for development and testing",
                "query_text": "Can we use client data (including PHI) to develop or test new services, and enhance, improve, or modify our existing services?",
                "category": "data_usage"
            },
            {
                "id": "2", 
                "title": "AI/ML restrictions in service delivery",
                "description": "Find restrictions on using artificial intelligence or machine learning",
                "query_text": "Are there any restrictions on using artificial intelligence or machine learning in delivering the services?",
                "category": "ai_ml"
            },
            {
                "id": "3",
                "title": "Cloud storage limitations for PHI",
                "description": "Search for limitations on storing client data including PHI in the cloud",
                "query_text": "Are there any limitations on storing client data (including PHI) in the cloud?",
                "category": "cloud_storage"
            },
            {
                "id": "4",
                "title": "Data retention requirements",
                "description": "Find data retention policies and timelines",
                "query_text": "What are the data retention requirements and timelines specified in the contracts?",
                "category": "retention"
            },
            {
                "id": "5",
                "title": "Client consent requirements for data use",
                "description": "Search for clauses requiring explicit client consent for data usage",
                "query_text": "Are there any clauses requiring explicit client consent for the use of their data in specific ways, such as for R&D purposes or AI training?",
                "category": "consent"
            },
            {
                "id": "6",
                "title": "Third-party vendor restrictions",
                "description": "Find restrictions on using third-party vendors or subcontractors",
                "query_text": "Are there any restrictions or requirements related to the use of third-party vendors or subcontractors in the processing of client data?",
                "category": "vendors"
            },
            {
                "id": "7",
                "title": "Human oversight requirements for AI",
                "description": "Search for requirements for human oversight in AI usage",
                "query_text": "Is there any requirement for human oversight or decision-making in the use of AI for delivering the services?",
                "category": "ai_oversight"
            },
            {
                "id": "8",
                "title": "IP ownership rights from client data",
                "description": "Find terms regarding ownership of IP developed from client data",
                "query_text": "Does the client have any ownership rights in developed IP or developed materials generated from the use of their data?",
                "category": "ip_ownership"
            }
        ]