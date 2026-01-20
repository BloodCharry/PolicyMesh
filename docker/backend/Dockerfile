FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./

RUN poetry export --without-hashes --without=dev --format=requirements.txt > requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app
COPY ./alembic /app/alembic
COPY alembic.ini /app/

COPY ./docker/backend/gunicorn_conf.py /app/gunicorn_conf.py
COPY ./docker/backend/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
