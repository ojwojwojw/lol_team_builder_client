FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY server/requirements-server.txt /tmp/requirements-server.txt

RUN pip install --no-cache-dir -r /tmp/requirements-server.txt

COPY server /app/server

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT}"]
