# AI Business Analyst Assistant 📊

A professional, production-ready system for financial data analysis. Upload your business data (Excel/CSV) and get AI-driven strategic insights verified by Python logic.

## Project Structure

- `backend/`: FastAPI + Polars + Qdrant + OpenAI GPT-4o
- `frontend/`: Next.js (App Router) + Lucide + CSS Glassmorphism

## Getting Started

### 1. Backend Setup

```bash
cd backend
# Install dependencies
uv sync
# Set your .env file with OPENAI_API_KEY
# Start the server
uv run python main.py
```

Backend runs at: `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
# Install dependencies
npm install
# Start the development server
npm run dev
```

Frontend runs at: `http://localhost:3000`

## Features

- **Accurate Math**: All calculations performed by Polars (Python), not the LLM.
- **RAG Powered**: Context-aware analysis using Qdrant vector database.
- **Structured Insights**: AI returns specific metrics, recommendations, and risks.
- **Premium UI**: Sleek, glassmorphism dashboard design.

## Verification

Run backend tests:

```bash
cd backend
uv run pytest tests/ -v
```

All 43 tests (unit + integration) should pass.
