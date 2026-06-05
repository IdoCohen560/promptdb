FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web
RUN pip install --no-cache-dir ".[web,providers]"

# Bake the sample DB so the image is self-contained (no curl in slim → use Python).
RUN python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite','chinook.db')"

ENV PROMPTDB_DATABASE_URL=sqlite:///chinook.db
EXPOSE 8000
# ANTHROPIC_API_KEY must be provided at runtime (host secret).
# Shell form so $PORT (injected by Render) expands; falls back to 8000 locally.
# --proxy-headers + forwarded-allow-ips so request.client.host is the real client IP behind
# Render's proxy (otherwise per-IP rate limiting buckets every user under the proxy's IP).
CMD uvicorn promptdb.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'
