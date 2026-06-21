FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AYUSHBOT_CONFIG=/app/backend/config.yaml

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt

COPY pyproject.toml README.md ./
COPY backend ./backend

RUN mkdir -p /app/var /app/models /app/backend/rag/index \
    && useradd --create-home --uid 10001 ayushbot \
    && chown -R ayushbot:ayushbot /app

USER ayushbot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ping', timeout=3)"

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
