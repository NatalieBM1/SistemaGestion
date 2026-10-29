FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run migrations then start the server.
# --proxy-headers + --forwarded-allow-ips: Render pone un proxy delante, así
# que sin esto request.client.host sería la IP del proxy para todos los
# usuarios y el límite de intentos (app/core/rate_limit.py) los bloquearía
# entre sí. Con esto uvicorn toma la IP real de X-Forwarded-For. '*' es
# seguro aquí porque el contenedor solo recibe tráfico a través del proxy.
CMD alembic upgrade head && python -m app.seed_auth && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
