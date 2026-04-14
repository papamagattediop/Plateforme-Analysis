# CensusAnalyse

![CensusAnalyse](https://img.shields.io/badge/CensusAnalyse-Django%20Microservices-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Plateforme d’analyse des données de recensement construite avec une architecture **microservices Django**. CensusAnalyse permet l’ingestion de fichiers, l’analyse statistique avancée et la visualisation interactive via des dashboards et des cartes.

---

## À propos

CensusAnalyse est un écosystème de trois services Django indépendants :

- `service_import` pour l’ingestion de données et les exports
- `service_analyse` pour les statistiques et les séries temporelles
- `service_visu` pour les cartes et les dashboards interactifs

L’architecture est conçue pour un déploiement Docker avec PostgreSQL, Redis et Celery, tout en restant exécutable en local en mode développement avec SQLite.

---

## Architecture globale

```text
CLIENT (Browser)
   │       │       │
   │       │       ├── service_visu (8003)
   │       ├── service_analyse (8002)
   └── service_import (8001)

service_import -> PostgreSQL import
service_analyse -> PostgreSQL analyse
service_visu -> PostgreSQL visu

Redis + Celery gèrent le traitement asynchrone des imports.
```

---

## Technologies principales

- Python 3.12
- Django 4.2
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Chart.js
- Folium / GeoPandas
- Docker + docker-compose

---

## Services

| Service | Port | Description |
|---|---|---|
| `service_import` | 8001 | Ingestion, nettoyage, export de datasets |
| `service_analyse` | 8002 | Statistiques univariées/bivariées et séries temporelles |
| `service_visu` | 8003 | Cartes géographiques, dashboards et export PDF |

---

## Structure du projet

```text
censusanalyse/
├── docker/
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── requirements.txt
├── .env.example
├── README.md
├── service_import/
├── service_analyse/
├── service_visu/
└── shared/
```

---

## Installation rapide

### 1. Préparation

```bash
cp .env.example .env
```

Éditez `.env` et remplacez les secrets, puis mettez `DEBUG=False` pour la production.

---

## Variables d'environnement

`.env.example` est un fichier de modèle. Si vous ne disposez pas encore de `.env`, copiez-le puis adaptez les valeurs :

```env
SECRET_KEY_IMPORT=replace-with-strong-secret
SECRET_KEY_ANALYSE=replace-with-strong-secret
SECRET_KEY_VISU=replace-with-strong-secret

DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

SERVICE_IMPORT_URL=http://service_import:8001
SERVICE_ANALYSE_URL=http://service_analyse:8002
SERVICE_VISU_URL=http://service_visu:8003

DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Conseils `.env`

- `SECRET_KEY_*` : utilisez des clés longues et uniques.
- `DEBUG` : `False` en production.
- `ALLOWED_HOSTS` : ajoutez les domaines publics de déploiement.
- `REDIS_URL` : en Docker, le service Redis est accessible via `redis://redis:6379/0`.

---

## Docker

### Lancer en développement

```bash
cd docker
docker-compose up --build -d
```

### Lancer en production

```bash
cd docker
docker-compose -f docker-compose.prod.yml up --build -d
```

### Notes Docker

- `docker/docker-compose.yml` démarre les trois services et Redis.
- `docker/docker-compose.prod.yml` ajoute la configuration de production avec `restart: unless-stopped`.
- Tous les services utilisent `env_file: ../.env` pour charger les variables d’environnement.
- Dans Docker, chaque service utilise `DB_HOST` pointant vers son propre conteneur PostgreSQL :
  - `service_import` → `db_import`
  - `service_analyse` → `db_analyse`
  - `service_visu` → `db_visu`

### Ports exposés

- `8001` → `service_import`
- `8002` → `service_analyse`
- `8003` → `service_visu`

---

## Endpoints principaux

### service_import

- `POST /api/v1/upload/`
- `GET /api/v1/datasets/`
- `GET /api/v1/datasets/<id>/data/`
- `GET /api/v1/datasets/<id>/export/<format>/`

### service_analyse

- `GET /api/v1/univariee/`
- `GET /api/v1/correlation/`
- `GET /api/v1/regression/`
- `GET /api/v1/prophet/`

### service_visu

- `POST /api/v1/cartes/choropletre/`
- `GET /api/v1/dashboards/`
- `POST /api/v1/dashboards/graphique/`
- `POST /api/v1/dashboards/<uuid>/export/pdf/`

---

### 2. Lancement avec Docker (recommandé)

```bash
cd docker
docker-compose up --build -d
```

### 3. Accès aux services

- `service_import` : http://localhost:8001
- `service_analyse` : http://localhost:8002
- `service_visu` : http://localhost:8003

---

## Déploiement production

```bash
cd docker
docker-compose -f docker-compose.prod.yml up --build -d
```

### À vérifier avant le déploiement

- `DEBUG=False`
- `ALLOWED_HOSTS` avec vos domaines publics
- `SECRET_KEY_IMPORT`, `SECRET_KEY_ANALYSE`, `SECRET_KEY_VISU` forts
- `DB_PASSWORD` unique et sécurisé

---

## Exécution locale sans Docker

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
cp .env.example .env
python service_import/manage.py migrate
python service_analyse/manage.py migrate
python service_visu/manage.py migrate
python service_import/manage.py runserver 8001
python service_analyse/manage.py runserver 8002
python service_visu/manage.py runserver 8003
```

> En mode dev sans Docker, chaque service utilise **SQLite** automatiquement.

---

## API principales

### service_import

- `POST /api/v1/upload/`
- `GET /api/v1/datasets/`
- `GET /api/v1/datasets/<id>/data/`
- `GET /api/v1/datasets/<id>/export/<format>/`

### service_analyse

- `GET /api/v1/univariee/`
- `GET /api/v1/correlation/`
- `GET /api/v1/regression/`
- `GET /api/v1/prophet/`

### service_visu

- `POST /api/v1/cartes/choropletre/`
- `GET /api/v1/dashboards/`
- `POST /api/v1/dashboards/graphique/`
- `POST /api/v1/dashboards/<uuid>/export/pdf/`

---

## Fonctionnalités clés

- Ingestion de fichiers (CSV, Excel, Stata, SPSS)
- Nettoyage et analyse automatique des colonnes
- Statistiques descriptives et tests statistiques
- Séries temporelles ARIMA / Prophet
- Dashboards interactifs et visualisations Chart.js
- Cartes choroplèthes et géo-visualisation
- Export PDF des dashboards

---

## Contribution

1. Forkez le dépôt
2. Créez une branche : `git checkout -b feature/mon-ajout`
3. Apportez vos modifications
4. Committez : `git commit -m "Ajout de ..."`
5. Poussez et ouvrez une Pull Request

---

## Licence

Ce projet est distribué sous licence MIT.
