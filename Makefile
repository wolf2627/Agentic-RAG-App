PORT ?= 8000

.PHONY: dev index test bot clean

dev:  ## Run development server with hot reload
	uv run uvicorn api:app --host 0.0.0.0 --port $(PORT) --reload

bot:  ## Run Telegram bot
	uv run python telegram_bot.py
	
index:  ## Index documents into vector database
	uv run python -m src.rag.ingest

# test:  ## Run tests
# 	uv run pytest

clean:  ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
