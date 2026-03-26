"""
urls.py — Dev 1 · Routes API
==============================
Toutes les routes du service Data Ingestion.
Préfixées avec /api/v1/ingestion/ dans le settings.py principal
pour éviter les conflits avec Dev 2 et Dev 3 lors de l'intégration.

Routes disponibles :
  POST   /api/upload/                          → Uploader un fichier
  GET    /api/datasets/                         → Lister les datasets
  GET    /api/datasets/{id}/                    → Détail complet
  GET    /api/datasets/{id}/data/               → Données nettoyées (pour Dev 2)
  PUT    /api/datasets/{id}/update/             → Modifier et sauvegarder
  DELETE /api/datasets/{id}/delete/             → Supprimer
  GET    /api/datasets/{id}/export/csv/         → Export CSV
  GET    /api/datasets/{id}/export/xlsx/        → Export Excel
  GET    /api/datasets/{id}/export/json/        → Export JSON
  GET    /api/datasets/{id}/traitements/        → Historique des traitements
  POST   /api/datasets/{id}/rollback/           → Annuler le dernier traitement
  GET    /api/datasets/{id}/summary/            → Résumé visuel (stats par colonne)
"""

from django.urls import path
from .views import (
    UploadView,
    DatasetListView,
    DatasetDetailView,
    DatasetDataView,
    DatasetUpdateView,
    DatasetDeleteView,
    DatasetExportView,
    TraitementsListView,
    DatasetRollbackView,
    DatasetSummaryView,
    DatasetColonnesView,
)

urlpatterns = [
    # ── Upload ──
    path('upload/',                                 UploadView.as_view(),         name='upload'),

    # ── Datasets ──
    path('datasets/',                               DatasetListView.as_view(),    name='datasets-list'),
    path('datasets/<int:pk>/',                      DatasetDetailView.as_view(),  name='dataset-detail'),
    path('datasets/<int:pk>/data/',                 DatasetDataView.as_view(),    name='dataset-data'),
    path('datasets/<int:pk>/update/',               DatasetUpdateView.as_view(),  name='dataset-update'),
    path('datasets/<int:pk>/delete/',               DatasetDeleteView.as_view(),  name='dataset-delete'),
    path('datasets/<int:pk>/summary/',              DatasetSummaryView.as_view(), name='dataset-summary'),

    # ── Export ──
    path('datasets/<int:pk>/export/<str:format_export>/', DatasetExportView.as_view(), name='dataset-export'),

    # ── Colonnes (endpoint léger pour Dev 2 et Dev 3) ──
    path('datasets/<int:pk>/colonnes/',             DatasetColonnesView.as_view(),  name='dataset-colonnes'),

    # ── Historique & rollback ──
    path('datasets/<int:pk>/traitements/',          TraitementsListView.as_view(),  name='traitements-list'),
    path('datasets/<int:pk>/rollback/',             DatasetRollbackView.as_view(), name='dataset-rollback'),
]
