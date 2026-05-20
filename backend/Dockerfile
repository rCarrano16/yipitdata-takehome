# Backend image: Python 3.12, installs the app package, runs the API.
FROM python:3.12-slim

WORKDIR /code

# Copy only what the package needs, then install it.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

EXPOSE 8000

# Seed the database once, then start the API server.
# app.seed and app.main are implemented in later build phases.
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
