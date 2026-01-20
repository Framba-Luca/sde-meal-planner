FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ./shared-lib /tmp/shared-lib
RUN pip install /tmp/shared-lib

COPY ./meal-planner-pcl/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Parte Codice (CAMBIA IL PATH)
COPY ./meal-planner-pcl .

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
