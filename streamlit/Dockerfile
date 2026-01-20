FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ./shared-lib /tmp/shared-lib
RUN pip install /tmp/shared-lib

COPY ./streamlit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./streamlit .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]