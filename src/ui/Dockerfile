FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/__init__.py ./src/
COPY src/ui/ ./src/ui/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "src.ui.api:app", "--host", "0.0.0.0", "--port", "8080"]
