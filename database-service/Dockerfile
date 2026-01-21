FROM python:3.11-slim

# Imposta variabili d'ambiente per Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice
COPY . .

# Espone la porta
EXPOSE 8002

# Avvio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]