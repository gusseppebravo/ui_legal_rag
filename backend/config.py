"""
Configuration for FastAPI backend integration
"""

import os

# FastAPI Backend Configuration
API_BASE_URL = os.getenv("RAG_API_URL", "http://localhost:8000")
API_KEY = os.getenv("RAG_API_KEY", "your-api-key-here")
REQUEST_TIMEOUT = 30

def get_headers():
    """Get headers for API requests"""
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

def get_endpoint(path: str) -> str:
    """Get full API endpoint URL"""
    return f"{API_BASE_URL}/{path.lstrip('/')}"
