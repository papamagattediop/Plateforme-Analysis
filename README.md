# CensusAnalyse

Plateforme d'analyse de données de recensement construite sur une architecture **microservices Django**. Elle permet l'ingestion de fichiers de données, l'analyse statistique avancée et la visualisation interactive (cartes choroplèthes, dashboards) — le tout via une API REST unifiée.

---

## Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                     │
└────────────┬─────────────────┬───────────────┬─────────────┘
             │                 │               │
      :8001  │          :8002  │        :8003  │
┌────────────▼───┐  ┌──────────▼──────┐  ┌────▼──────────────┐
│ service_import │  │ service_analyse │  │   service_visu    │
│   (Dev 1)      │◄─┤   (Dev 2)       │◄─┤   (Dev 3)         │
│                │  │                 │  │                   │
│  import_app    │  │  stats_app      │  │  dashboard_app    │
│                │  │  series_app     │  │  cartes_app       │
│                │  │  tests_stat_app │  │                   │
└───────┬────────┘  └────────┬────────┘  └─────────┬─────────┘
        │                    │                      │
   ┌────▼────┐          ┌────▼────┐           ┌────▼────┐
   │  PG DB  │          │  PG DB  │           │  PG DB  │
   │ import  │          │ analyse │           │  visu   │
   └─────────┘          └─────────┘           └─────────┘
        │
   ┌────▼──────────┐
   │ Redis + Celery│  (traitement asynchrone des fichiers)
   └───────────────┘
```

---

## Services

| Service | Port | Rôle |
|---|---|---|
| `service_import` | 8001 | Upload, détection de types, nettoyage, export |
| `service_analyse` | 8002 | Statistiques descriptives, tests, séries temporelles |
| `service_visu` | 8003 | Cartes choroplèthes, dashboards, export PDF |

---

## Structure du projet

```
censusanalyse/
├── docker-compose.yml
├── requirements.txt                  ← dépendances unifiées
├── .env.example
├── README.md
│
├── service_import/                   ── Dev 1 · Ingestion (port 8001)
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── import_app/
│   │   ├── models.py                 (Dataset, ColonneInfo, TraitementLog, ExportLog)
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── tasks.py                  (Celery async)
│   │   └── utils.py
│   ├── frontend/
│   │   ├── static/
│   │   └── templates/
│   └── manage.py
│
├── service_analyse/                  ── Dev 2 · Analyse (port 8002)
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── stats_app/                    (Statistiques univariées & bivariées)
│   │   ├── engines/stats.py
│   │   ├── selector.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── series_app/                   (Séries temporelles — ARIMA, Prophet)
│   │   ├── engines/series.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── tests_stat_app/               (Sélecteur de tests statistiques)
│   │   ├── engines/tests.py
│   │   ├── selector.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── frontend/
│   └── manage.py
│
├── service_visu/                     ── Dev 3 · Visualisation (port 8003)
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── cartes_app/                   (Cartes Folium — choroplèthe, heatmap, points)
│   │   ├── models.py                 (GeoJSONRegion, CarteGeneree)
│   │   ├── engines/maps.py
│   │   ├── management/commands/charger_geojson.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── dashboard_app/                (Constructeur de dashboards)
│   │   ├── models.py                 (Dashboard, Widget)
│   │   ├── engines/builder.py
│   │   ├── engines/export.py         (PDF via ReportLab)
│   │   ├── views.py
│   │   └── urls.py
│   ├── senegal.geojson
│   ├── senegal_regions.geojson
│   ├── frontend/
│   └── manage.py
│
└── shared/
    ├── api_contracts/openapi.yaml    ← contrat OpenAPI inter-services
    └── mocks/
        ├── import_mock.py
        └── analyse_mock.py
```

---

## API Reference

### service_import — `http://localhost:8001/api/v1/`

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/upload/` | Upload CSV / Excel / Stata / SPSS |
| `GET` | `/datasets/` | Lister tous les datasets |
| `GET` | `/datasets/<id>/` | Détail d'un dataset |
| `GET` | `/datasets/<id>/data/` | Données nettoyées (paginées) |
| `GET` | `/datasets/<id>/colonnes/` | Métadonnées des colonnes |
| `GET` | `/datasets/<id>/summary/` | Résumé statistique par colonne |
| `GET` | `/datasets/<id>/export/<format>/` | Export (csv / xlsx / json) |
| `GET` | `/datasets/<id>/traitements/` | Historique des traitements |
| `POST` | `/datasets/<id>/rollback/` | Annuler le dernier traitement |

### service_analyse — `http://localhost:8002/api/v1/`

**Statistiques univariées**

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/univariee/` | Stats descriptives |
| `GET` | `/ic/` | Intervalles de confiance |
| `GET` | `/normalite/` | Test de normalité (Shapiro-Wilk, K-S) |
| `GET` | `/histogramme/` | Histogramme |
| `GET` | `/boxplot/` | Boîte à moustaches |
| `GET` | `/frequences/` | Distribution de fréquences (catégorielle) |

**Statistiques bivariées**

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/correlation/` | Corrélation Pearson / Spearman |
| `GET` | `/regression/` | Régression linéaire |
| `GET` | `/regression-poly/` | Régression polynomiale |
| `GET` | `/matrice-correlation/` | Matrice de corrélation |
| `GET` | `/scatter/` | Nuage de points |
| `GET` | `/contingence/` | Table de contingence |
| `GET` | `/stats-groupees/` | Stats par groupe |
| `GET` | `/anova/` | ANOVA one-way |
| `GET` | `/ttest/` | Test t de Student |
| `GET` | `/mann-whitney/` | Test de Mann-Whitney U |
| `GET` | `/kruskal/` | Test de Kruskal-Wallis |

**Tests statistiques**

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/tests/normalite/` | Sélecteur de test de normalité |
| `POST` | `/tests/comparaison/` | Sélecteur de test de comparaison |
| `POST` | `/tests/independance/` | Test du Chi² / Fisher exact |
| `GET` | `/tests/selectionner/` | Outil interactif de sélection |

**Séries temporelles**

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/stationarity/` | Test ADF (Augmented Dickey-Fuller) |
| `GET` | `/arima/` | Prévision ARIMA |
| `GET` | `/prophet/` | Prévision Facebook Prophet |

### service_visu — `http://localhost:8003/api/v1/`

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/cartes/choropletre/` | Carte choroplèthe |
| `POST` | `/cartes/heatmap/` | Carte de chaleur |
| `POST` | `/cartes/points/` | Carte de points |
| `POST` | `/cartes/comparaison/` | Comparaison deux variables |
| `GET` | `/cartes/share/<token>/` | Carte publique partageable |
| `GET` | `/dashboards/` | Lister les dashboards |
| `GET` | `/dashboards/<uuid>/` | Détail d'un dashboard |
| `POST` | `/dashboards/graphique/` | Prévisualiser un graphique |
| `POST` | `/dashboards/<uuid>/export/pdf/` | Exporter en PDF |
| `GET` | `/dashboards/share/<token>/` | Dashboard public partageable |

---

## Démarrage rapide

### Avec Docker (recommandé)

```bash
# 1. Copier les variables d'environnement
cp .env.example .env

# 2. Construire et lancer tous les services
docker-compose up --build

# 3. Accéder aux services
#    service_import  → http://localhost:8001
#    service_analyse → http://localhost:8002
#    service_visu    → http://localhost:8003
```

### Sans Docker (développement local)

```bash
# 1. Créer et activer le venv global
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Copier les variables d'environnement
cp .env.example .env

# 4. Appliquer les migrations (SQLite en mode dev)
python service_import/manage.py migrate
python service_analyse/manage.py migrate
python service_visu/manage.py migrate

# 5. Lancer les 3 services (3 terminaux)
python service_import/manage.py runserver 8001
python service_analyse/manage.py runserver 8002
python service_visu/manage.py runserver 8003
```

> En mode dev sans Docker, chaque service utilise **SQLite** automatiquement (aucune configuration PostgreSQL requise).

---

## Stack technique

| Catégorie | Technologies |
|---|---|
| Backend | Django 4.2+, Django REST Framework |
| Calcul statistique | Pandas, NumPy, SciPy, Statsmodels, scikit-learn |
| Séries temporelles | ARIMA (statsmodels), Prophet |
| Cartographie | Folium, GeoPandas, GeoJSON Sénégal |
| Visualisation | Chart.js, Plotly |
| Tâches async | Celery + Redis |
| Base de données | PostgreSQL (une par service) / SQLite (dev) |
| Export | ReportLab (PDF), OpenPyXL (Excel) |
| Conteneurisation | Docker + docker-compose |

---

## Variables d'environnement

Copier `.env.example` en `.env` et renseigner les valeurs :

```env
SECRET_KEY_IMPORT=...
SECRET_KEY_ANALYSE=...
SECRET_KEY_VISU=...

DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

SERVICE_IMPORT_URL=http://service_import:8001
SERVICE_ANALYSE_URL=http://service_analyse:8002
SERVICE_VISU_URL=http://service_visu:8003

DEBUG=True
```

---

## Formats de fichiers supportés

`CSV` · `Excel (.xlsx)` · `Stata (.dta)` · `SPSS (.sav)`

---

## Auteur

**Papa Magatte Diop** — ENSAE Dakar, Cycle AS3
