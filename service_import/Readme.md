# Service Import — API Django

Ce projet fournit un service d’ingestion de données (upload, export, rollback, logs) exposé via une API REST.
Il est conçu par **Dev1** et destiné à être utilisé par **Dev2** (analyse) et **Dev3** (visualisation).

---

## 🚀 Prérequis

- [Docker](https://docs.docker.com/get-docker/) installé
- [Docker Compose](https://docs.docker.com/compose/) installé
- Port **8001** disponible sur votre machine

---

## 📂 Structure du projet

service_import/
├── import_app/          # Application Django
├── service_import/      # Configuration Django (settings, urls, etc.)
├── manage.py            # Script Django
├── requirements.txt     # Dépendances Python
├── Dockerfile           # Image Docker pour l’API
├── docker-compose.yml   # Orchestration API + PostgreSQL + Redis
└── README.md            # Documentation


## ⚙️ Lancer le projet

### 1. Construire et démarrer les services
Depuis la racine du projet :

```bash
docker-compose up --build


### Arret
docker-compose down