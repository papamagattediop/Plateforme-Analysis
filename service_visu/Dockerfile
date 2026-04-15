FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-bin \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8003
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --no-input && python manage.py charger_geojson --fichier senegal_regions.geojson --nom senegal_regions --label 'Régions du Sénégal' --niveau region --cle_join NAME_1 && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8003} --workers 2 --timeout 120"]
