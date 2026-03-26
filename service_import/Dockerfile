# ───────────────────────────────────────────────
# Dockerfile — Service Import (Dev1)
# ───────────────────────────────────────────────

# 1. Image de base : Python 3.11, version slim (Debian minimal)
FROM python:3.11-slim

# 2. Variables d’environnement utiles
# - PYTHONDONTWRITEBYTECODE : évite la création de fichiers .pyc
# - PYTHONUNBUFFERED : affiche les logs immédiatement (pas de buffer)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Répertoire de travail dans le conteneur
WORKDIR /app

# 4. Installer les dépendances système nécessaires
# - gcc : compilateur pour certaines librairies Python
# - libpq-dev : client PostgreSQL (nécessaire pour psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copier le fichier requirements.txt
COPY requirements.txt .

# 6. Installer les dépendances Python listées dans requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copier tout le code source du projet dans le conteneur
COPY . .

# 8. Créer un dossier pour stocker les fichiers uploadés (media)
RUN mkdir -p /app/media/uploads

# 9. Exposer le port sur lequel Django va tourner
EXPOSE 8001

# 10. Commande de démarrage
# - migrate : crée les tables si elles n'existent pas encore
# - gunicorn : serveur WSGI production (2 workers)
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --no-input && gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers 2 --timeout 120"]
