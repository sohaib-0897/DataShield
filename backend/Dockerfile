FROM python:3.11-slim
WORKDIR /app
ENV PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r /app/backend/requirements.txt
COPY backend /app/backend
COPY legacy /app/legacy
COPY ml /app/ml
COPY scripts /app/scripts
COPY alembic.ini /app/alembic.ini
ENV PYTHONPATH=/app/backend:/app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000"]
