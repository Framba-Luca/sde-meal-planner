FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ./shared-lib /tmp/shared-lib
RUN pip install /tmp/shared-lib

COPY ./database-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./database-service .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]