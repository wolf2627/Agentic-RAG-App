# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:/root/.local/bin:/root/.cargo/bin:${PATH}"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    curl \
    libxml2-dev \
    libxslt1-dev \
    libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (https://github.com/astral-sh/uv)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    (ln -sf /root/.local/bin/uv /usr/local/bin/uv || true) && \
    (ln -sf /root/.cargo/bin/uv /usr/local/bin/uv || true) && \
    uv --version

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Create directories for documents and embeddings if they don't exist
RUN mkdir -p /app/documents /app/embeddings

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
