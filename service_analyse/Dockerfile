FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends gcc libpq-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser requirements.txt .

USER appuser

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser service_analyse .

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -m requests.get http://localhost:8002/health || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8002", "--workers", "2", "--timeout", "120"]