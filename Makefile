PORT ?= 8000

.PHONY: dev index test

dev:  ## Run development server with hot reload
	uv run uvicorn rag.app:app --host 0.0.0.0 --port $(PORT) --reload
	
index:
	uv run python -m rag.ingest
