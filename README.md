# Legal RAG UI

Streamlit interface for searching legal documents using AI-powered retrieval.

## Quick Start

```bash
uv run streamlit run app.py
```

Open http://localhost:8501 to use the application.

## Features

- Search 17,374+ legal document chunks
- Filter by 120+ clients
- AI-generated answers with source citations
- Direct PDF access via presigned URLs
- Predefined legal queries

## Architecture

- **Frontend**: Streamlit UI
- **Backend**: AWS S3 Vector Store + Azure OpenAI
- **Embeddings**: e5_mistral_embed_384 model
- **Documents**: Legal contracts, addendums, SOWs

## Testing

```bash
uv run python test_rag.py
```
