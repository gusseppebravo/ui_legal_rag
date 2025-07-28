# Legal Document Search UI

A Streamlit application for legal document search with FastAPI RAG backend integration.

## Features

- **Document Search**: Predefined queries and custom search with client filtering
- **Document Viewer**: Full document viewing with navigation
- **FastAPI Integration**: Ready for containerized RAG backend services

## Quick Start

1. Install dependencies:
```bash
uv sync
```

2. Run the application:
```bash
uv run streamlit run app.py
```

## Backend Integration

The UI connects to a FastAPI RAG service with these endpoints:

- `GET /queries` - Get predefined queries
- `GET /clients` - Get available clients  
- `POST /search` - Search documents (payload: `{"query": "...", "client_filter": "..."}`)
- `GET /documents/{id}` - Get full document

Update `backend/config.py` with your FastAPI service URL:
```python
API_BASE_URL = "http://localhost:8000"  # Your FastAPI service
API_KEY = "your-api-key"               # Optional API key
```

The application includes a mock mode for development. Set `use_mock = False` in `backend/fastapi_client.py` when your FastAPI service is ready.

## Architecture

```
├── app.py                    # Main Streamlit app
├── backend/
│   ├── fastapi_client.py     # FastAPI client with mock mode
│   ├── models.py             # Data models
│   └── config.py             # API configuration
├── pages/                    # UI pages
└── utils/                    # UI components and helpers
```
