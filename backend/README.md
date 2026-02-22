# AI Business Analyst Assistant

A production-ready AI agent designed to analyze financial data from Excel and CSV files using natural language.

## 🚀 Technology Stack

- **Backend**: FastAPI (Python 3.12+)
- **Data Engine**: [Polars](https://pola.rs/) (High-performance data manipulation)
- **Excel Engine**: Calamine (Rust-based Excel parser)
- **Vector Database**: [Qdrant](https://qdrant.tech/) (Vector similarity search)
- **LLM**: OpenAI GPT-4o / GPT-4
- **ORM/Schema**: Pydantic v2
- **Environment Management**: [uv](https://github.com/astral-sh/uv)

## 🛠️ Key Features

- **Blazing Fast Parsing**: Uses Rust-powered engines to parse multi-sheet Excel files.
- **Accurate Analytics**: All math is performed by Polars Expression API, preventing LLM calculation errors.
- **RAG Implementation**: Retrieves relevant context from financial documents using Qdrant.
- **Thai & English Support**: Bilingual natural language processing for business insights.

## 📦 Getting Started

### Prerequisites

- Python 3.12+
- `uv` package manager

### Installation

```bash
cd backend
uv sync --all-groups
```

### Running the App

```bash
uv run uvicorn main:app --reload
```

### Running Tests

```bash
uv run pytest tests/ -v
```

## 📖 Project Structure

See `CLAUDE.md` for detailed coding standards and architecture.
