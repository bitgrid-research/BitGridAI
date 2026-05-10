FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/__init__.py ./src/
COPY src/main.py ./src/
COPY src/production_runner.py ./src/
COPY src/core/ ./src/core/
COPY src/adapters/ ./src/adapters/
COPY src/data/ ./src/data/
COPY src/ops/ ./src/ops/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]
