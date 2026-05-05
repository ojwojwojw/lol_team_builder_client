FROM python:3.11-slim

WORKDIR /app

# 서버 requirements만 복사
COPY server/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 서버 코드만 복사
COPY server/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]