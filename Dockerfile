FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AEGIS_EMBEDDING_BACKEND=local

WORKDIR /app

# Dependencies first so corpus/code edits don't invalidate the pip layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the index at image-build time: the container starts ready to serve, so
# the first demo turn never pays an indexing cost that would land in TTFT.
RUN python -m corpus.build_index

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=4s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health',timeout=3).status==200 else 1)"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
