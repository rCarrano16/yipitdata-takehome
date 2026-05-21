# Backend image: Python 3.12, installs the app package, runs the API.
FROM python:3.12-slim

WORKDIR /code

# Copy only what the package needs, then install it.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

EXPOSE 8000

# Seed the database (idempotent), then start the API server. The CSV is bind
# mounted at /data by docker-compose.yml, since it lives at the repo root,
# outside this build context. uvicorn's plaintext access log is off because the
# request-logging middleware already emits one JSON line per request.
CMD ["sh", "-c", "python -m app.seed --csv /data/kpi_sample_2000.csv && uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"]
