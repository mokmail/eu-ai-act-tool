# Server image: FastAPI + the eu_ai_act package.
# Build context is the REPO ROOT (the server depends on the parent package by path).
#   docker build -f server/Dockerfile -t eu-ai-act-server .

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# The parent package (installed as an editable path dependency of the server).
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# The server project.
COPY server ./server
WORKDIR /app/server
RUN uv sync --no-dev

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
