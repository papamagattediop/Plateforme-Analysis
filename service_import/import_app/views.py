"""
views.py — Dev 1 · Vues API
============================
Expose tous les endpoints du service Data Ingestion :

  POST   /api/upload/                        → Uploader et traiter un fichier
  GET    /api/datasets/                       → Lister tous les datasets
  GET    /api/datasets/{id}/                  → Détails d'un dataset (colonnes, logs)
  GET    /api/datasets/{id}/data/             → Données nettoyées en JSON (pour Dev 2)
  PUT    /api/datasets/{id}/update/           → Modifier une/des valeur(s) et sauvegarder
  DELETE /api/datasets/{id}/delete/           → Supprimer un dataset
  GET    /api/datasets/{id}/export/{format}/  → Exporter en CSV, Excel ou JSON
  GET    /api/datasets/{id}/traitements/      → Historique des traitements
  POST   /api/datasets/{id}/rollback/         → Annuler le dernier traitement
  GET    /api/datasets/{id}/summary/          → Résumé visuel (stats par colonne)
"""

import io
import json
import pandas as pd

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Dataset, ColonneInfo, TraitementLog, ExportLog
from .serializers import (
    DatasetListSerializer,
    DatasetDetailSerializer,
    TraitementLogSerializer,
)
from .utils import (
    lire_fichier,
    nettoyer_dataframe,
    detect_types,
    stats_colonne,
    dataframe_to_json,
)

# Seuil au-delà duquel le traitement passe en mode asynchrone (Celery)
SEUIL_ASYNC_OCTETS = 2 * 1024 * 1024  # 2 Mo


# ══════════════════════════════════════════════
# HELPER — réponse standardisée
# ══════════════════════════════════════════════
def ok(data=None, message="", status_code=200):
    """Réponse succès standardisée pour toute l'API."""
    return Response({'status': 'success', 'message': message, 'data': data}, status=status_code)

def err(message, status_code=400, details=None):
    """Réponse erreur standardisée."""
    return Response({'status': 'error', 'message': message, 'details': details}, status=status_code)


# ══════════════════════════════════════════════
# 1. UPLOAD — POST /api/upload/
# ══════════════════════════════════════════════
class UploadView(APIView):
    """
    Reçoit un fichier CSV ou Excel, le nettoie, détecte les types
    et sauvegarde toutes les métadonnées en base.

    Body (multipart/form-data):
        fichier: <fichier CSV ou Excel>

    Réponse 201:
        {
          "dataset_id": 42,
          "nb_lignes": 1185,
          "nb_colonnes": 8,
          "has_date": true,
          "colonnes": {"age": "numeric", "date_naissance": "datetime", ...},
          "rapport_nettoyage": {...}
        }
    """

    def post(self, request):
        # ── Récupérer le fichier ──
        fichier = request.FILES.get('fichier')
        if not fichier:
            return err("Aucun fichier fourni. Utilisez le champ 'fichier'.")

        # ── Fichier volumineux → traitement asynchrone (Celery) ──
        if fichier.size > SEUIL_ASYNC_OCTETS:
            dataset = Dataset.objects.create(
                nom_fichier = fichier.name,
                fichier     = fichier,
                statut      = 'en_attente',
            )
            try:
                from .tasks import traiter_fichier_async
                traiter_fichier_async.delay(dataset.id)
                mode = 'async'
            except Exception:
                # Si Celery non disponible, traitement synchrone de secours
                mode = 'sync_fallback'
                _traiter_synchrone(dataset, fichier)

            return ok({
                'dataset_id': dataset.id,
                'statut':     dataset.statut,
                'mode':       mode,
                'message':    'Fichier en cours de traitement. Consultez /api/datasets/{id}/status/ pour suivre l\'avancement.',
            }, message="Fichier reçu — traitement en arrière-plan.", status_code=202)

        # ── Fichier léger → traitement synchrone immédiat ──
        try:
            df = lire_fichier(fichier)
        except ValueError as e:
            return err(str(e))

        if df.empty:
            return err("Le fichier est vide ou ne contient pas de données lisibles.")

        df, rapport = nettoyer_dataframe(df)
        types    = detect_types(df)
        has_date = 'datetime' in types.values()
        # Convertir les colonnes détectées comme datetime en datetime64 réel
        for col, t in types.items():
            if t == 'datetime' and df[col].dtype == object:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass
        donnees_json = dataframe_to_json(df.copy())

        dataset = Dataset.objects.create(
            nom_fichier       = fichier.name,
            fichier           = fichier,
            nb_lignes         = len(df),
            nb_colonnes       = len(df.columns),
            has_date          = has_date,
            statut            = 'traite',
            rapport_nettoyage = rapport,
            donnees_json      = donnees_json,
        )

        for nom_col, type_col in types.items():
            stats = stats_colonne(df, nom_col)
            ColonneInfo.objects.create(
                dataset               = dataset,
                nom                   = nom_col,
                type_detecte          = type_col,
                nb_valeurs_manquantes = stats['nb_valeurs_manquantes'],
                nb_valeurs_uniques    = stats['nb_valeurs_uniques'],
                exemple_valeurs       = stats['exemple_valeurs'],
            )

        TraitementLog.objects.create(
            dataset         = dataset,
            type_traitement = 'import',
            description     = f"Import initial du fichier '{fichier.name}'",
            details         = rapport,
        )

        return ok({
            'dataset_id':        dataset.id,
            'nb_lignes':         len(df),
            'nb_colonnes':       len(df.columns),
            'has_date':          has_date,
            'colonnes':          types,
            'rapport_nettoyage': rapport,
        }, message="Fichier importé et traité avec succès.", status_code=201)


def _traiter_synchrone(dataset, fichier):
    """Traitement de secours si Celery n'est pas disponible."""
    try:
        df, rapport = nettoyer_dataframe(lire_fichier(fichier))
        types    = detect_types(df)
        has_date = 'datetime' in types.values()
        for col, t in types.items():
            if t == 'datetime' and df[col].dtype == object:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass
        dataset.nb_lignes         = len(df)
        dataset.nb_colonnes       = len(df.columns)
        dataset.has_date          = has_date
        dataset.rapport_nettoyage = rapport
        dataset.donnees_json      = dataframe_to_json(df.copy())
        dataset.statut            = 'traite'
        dataset.save()
        for nom_col, type_col in types.items():
            stats = stats_colonne(df, nom_col)
            ColonneInfo.objects.create(
                dataset=dataset, nom=nom_col, type_detecte=type_col,
                nb_valeurs_manquantes=stats['nb_valeurs_manquantes'],
                nb_valeurs_uniques=stats['nb_valeurs_uniques'],
                exemple_valeurs=stats['exemple_valeurs'],
            )
    except Exception as e:
        dataset.statut = 'erreur'
        dataset.rapport_nettoyage = {'erreur': str(e)}
        dataset.save()


# ══════════════════════════════════════════════
# 2. LISTE DES DATASETS — GET /api/datasets/
# ══════════════════════════════════════════════
class DatasetListView(APIView):
    """
    Retourne la liste de tous les datasets uploadés.
    Version légère : sans les données ni les colonnes détaillées.
    """

    def get(self, request):
        datasets = Dataset.objects.all()
        serializer = DatasetListSerializer(datasets, many=True)
        return ok(serializer.data)


# ══════════════════════════════════════════════
# 3. DÉTAIL D'UN DATASET — GET /api/datasets/{id}/
# ══════════════════════════════════════════════
class DatasetDetailView(APIView):
    """
    Retourne les métadonnées complètes d'un dataset :
    colonnes détectées, rapport de nettoyage, historique des traitements.
    NE retourne PAS les données brutes (→ utiliser /data/).
    """

    def get(self, request, pk):
        try:
            dataset = Dataset.objects.prefetch_related('colonnes', 'traitements', 'exports').get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        serializer = DatasetDetailSerializer(dataset)
        return ok(serializer.data)


# ══════════════════════════════════════════════
# 4. DONNÉES NETTOYÉES — GET /api/datasets/{id}/data/
#    C'est l'endpoint principal consommé par Dev 2
# ══════════════════════════════════════════════
class DatasetDataView(APIView):
    """
    Retourne les données nettoyées du dataset au format JSON.
    Cet endpoint est principalement appelé par Dev 2 (Analytics Engine)
    pour récupérer les données à analyser.

    Query params optionnels:
        ?limit=100    → Limiter le nombre de lignes retournées
        ?offset=0     → Décalage pour la pagination
        ?colonnes=a,b → Filtrer sur certaines colonnes seulement
    """

    def get(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        if dataset.statut != 'traite':
            return err(f"Le dataset n'est pas encore traité (statut: {dataset.statut}).")

        # Récupérer les données stockées
        donnees = dataset.donnees_json

        # ── Filtrage des colonnes (optionnel) ──
        colonnes_demandees = request.query_params.get('colonnes')
        if colonnes_demandees:
            cols = [c.strip() for c in colonnes_demandees.split(',')]
            donnees = [{k: v for k, v in row.items() if k in cols} for row in donnees]

        # ── Pagination (optionnel) ──
        try:
            limit  = int(request.query_params.get('limit', len(donnees)))
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            return err("Les paramètres 'limit' et 'offset' doivent être des entiers.")

        donnees_paginee = donnees[offset: offset + limit]

        return ok({
            'dataset_id':  dataset.id,
            'has_date':    dataset.has_date,   # Dev 2 utilise ce flag pour activer M5
            'nb_total':    len(donnees),
            'nb_retourne': len(donnees_paginee),
            'offset':      offset,
            'colonnes':    [c.nom for c in dataset.colonnes.all()],
            'donnees':     donnees_paginee,
        })


# ══════════════════════════════════════════════
# 5. MODIFICATION DES DONNÉES — PUT /api/datasets/{id}/update/
#    Sauvegarde les modifications + log dans TraitementLog
# ══════════════════════════════════════════════
class DatasetUpdateView(APIView):
    """
    Permet de modifier les données d'un dataset et de sauvegarder
    les changements avec un log dans TraitementLog.

    Body JSON:
        {
          "type_traitement": "suppression_doublons",
          "description": "Suppression manuelle des doublons sur colonne 'id'",
          "donnees": [...],     ← nouvelles données complètes
          "details": {...}      ← détails optionnels du traitement
        }

    Le snapshot des données AVANT modification est sauvegardé
    pour permettre un rollback.
    """

    def put(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        # ── Valider les champs obligatoires ──
        type_traitement = request.data.get('type_traitement', 'autre')
        description     = request.data.get('description', 'Modification manuelle')
        nouvelles_donnees = request.data.get('donnees')
        details         = request.data.get('details', {})

        if nouvelles_donnees is None:
            return err("Le champ 'donnees' est obligatoire.")

        if not isinstance(nouvelles_donnees, list):
            return err("Le champ 'donnees' doit être une liste de dicts JSON.")

        # ── Snapshot des données AVANT modification (pour rollback) ──
        snapshot_avant = dataset.donnees_json

        # ── Appliquer les nouvelles données ──
        dataset.donnees_json = nouvelles_donnees
        dataset.nb_lignes    = len(nouvelles_donnees)
        dataset.date_modif   = None  # auto_now=True le mettra à jour
        dataset.save()

        # ── Enregistrer dans l'historique ──
        log = TraitementLog.objects.create(
            dataset          = dataset,
            type_traitement  = type_traitement,
            description      = description,
            details          = details,
            snapshot_avant   = snapshot_avant,  # Permet le rollback
        )

        return ok({
            'dataset_id':    dataset.id,
            'nb_lignes':     dataset.nb_lignes,
            'log_id':        log.id,
        }, message="Données mises à jour et sauvegardées.")


# ══════════════════════════════════════════════
# 6. ROLLBACK — POST /api/datasets/{id}/rollback/
#    Annuler le dernier traitement
# ══════════════════════════════════════════════
class DatasetRollbackView(APIView):
    """
    Annule le dernier traitement effectué sur un dataset
    en restaurant le snapshot sauvegardé dans TraitementLog.

    Utile pour annuler une suppression de doublons ou une modification.
    """

    def post(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        # Récupérer le dernier log avec un snapshot
        dernier_log = (
            TraitementLog.objects
            .filter(dataset=dataset)
            .exclude(snapshot_avant=[])  # Ignorer les logs sans snapshot
            .order_by('-date_traitement')
            .first()
        )

        if not dernier_log:
            return err("Aucun traitement précédent à annuler.")

        if not dernier_log.snapshot_avant:
            return err("Le dernier traitement n'a pas de snapshot disponible pour rollback.")

        # ── Restaurer les données du snapshot ──
        dataset.donnees_json = dernier_log.snapshot_avant
        dataset.nb_lignes    = len(dernier_log.snapshot_avant)
        dataset.save()

        # ── Supprimer le log annulé ──
        log_description = dernier_log.description
        dernier_log.delete()

        return ok({
            'dataset_id': dataset.id,
            'nb_lignes':  dataset.nb_lignes,
        }, message=f"Rollback effectué. Traitement annulé : '{log_description}'")


# ══════════════════════════════════════════════
# 7. EXPORT — GET /api/datasets/{id}/export/{format}/
#    Formats supportés : csv, xlsx, json
# ══════════════════════════════════════════════
class DatasetExportView(APIView):
    """
    Exporte le dataset dans le format demandé.
    Enregistre l'export dans ExportLog.

    URL: /api/datasets/{id}/export/csv/
         /api/datasets/{id}/export/xlsx/
         /api/datasets/{id}/export/json/
    """

    FORMATS_SUPPORTES = ['csv', 'xlsx', 'json']

    def get(self, request, pk, format_export):
        # ── Valider le format ──
        if format_export not in self.FORMATS_SUPPORTES:
            return err(f"Format '{format_export}' non supporté. Choisir parmi : {self.FORMATS_SUPPORTES}")

        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        if not dataset.donnees_json:
            return err("Aucune donnée disponible pour cet export.")

        # ── Reconstruire le DataFrame depuis le JSON stocké ──
        df = pd.DataFrame(dataset.donnees_json)

        nom_base = dataset.nom_fichier.rsplit('.', 1)[0]  # Sans extension

        # ── Export CSV ──
        if format_export == 'csv':
            buffer = io.StringIO()
            df.to_csv(buffer, index=False, encoding='utf-8-sig')  # utf-8-sig pour Excel
            response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{nom_base}_export.csv"'

        # ── Export Excel ──
        elif format_export == 'xlsx':
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Données')
                # Feuille secondaire : rapport de nettoyage
                rapport_df = pd.DataFrame([dataset.rapport_nettoyage])
                rapport_df.to_excel(writer, index=False, sheet_name='Rapport nettoyage')
            response = HttpResponse(
                buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{nom_base}_export.xlsx"'

        # ── Export JSON ──
        elif format_export == 'json':
            export_data = {
                'dataset':   {'id': dataset.id, 'nom': dataset.nom_fichier, 'has_date': dataset.has_date},
                'colonnes':  [{'nom': c.nom, 'type': c.type_detecte} for c in dataset.colonnes.all()],
                'donnees':   dataset.donnees_json,
                'traitements': [
                    {'type': t.type_traitement, 'description': t.description, 'date': str(t.date_traitement)}
                    for t in dataset.traitements.all()
                ]
            }
            response = HttpResponse(
                json.dumps(export_data, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="{nom_base}_export.json"'

        # ── Enregistrer l'export dans ExportLog ──
        ExportLog.objects.create(dataset=dataset, format_export=format_export)

        return response


# ══════════════════════════════════════════════
# 8. HISTORIQUE — GET /api/datasets/{id}/traitements/
# ══════════════════════════════════════════════
class TraitementsListView(APIView):
    """
    Retourne l'historique complet des traitements effectués sur un dataset.
    Permet de visualiser toutes les modifications (import, nettoyage, corrections...).
    """

    def get(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        logs = dataset.traitements.all()
        serializer = TraitementLogSerializer(logs, many=True)
        return ok({
            'dataset_id': pk,
            'nb_traitements': logs.count(),
            'traitements': serializer.data,
        })


# ══════════════════════════════════════════════
# 9. RÉSUMÉ VISUEL — GET /api/datasets/{id}/summary/
#    Stats descriptives rapides par colonne (pour Dev 3 ou affichage)
# ══════════════════════════════════════════════
class DatasetSummaryView(APIView):
    """
    Retourne un résumé statistique rapide par colonne.
    Utile pour visualiser la structure du dataset avant analyse.

    Réponse :
        {
          "nb_lignes": 1185,
          "nb_colonnes": 8,
          "has_date": true,
          "colonnes": [
            {
              "nom": "age",
              "type": "numeric",
              "nb_manquantes": 3,
              "nb_uniques": 72,
              "exemples": [23, 45, 67]
            },
            ...
          ],
          "traitements_appliques": ["import", "suppression_doublons"]
        }
    """

    def get(self, request, pk):
        try:
            dataset = Dataset.objects.prefetch_related('colonnes', 'traitements').get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        # Résumé des colonnes
        colonnes_summary = [
            {
                'nom':           c.nom,
                'type':          c.type_detecte,
                'nb_manquantes': c.nb_valeurs_manquantes,
                'nb_uniques':    c.nb_valeurs_uniques,
                'exemples':      c.exemple_valeurs,
            }
            for c in dataset.colonnes.all()
        ]

        # Types de traitements appliqués
        types_traitements = list(
            dataset.traitements.values_list('type_traitement', flat=True).distinct()
        )

        return ok({
            'dataset_id':           dataset.id,
            'nom_fichier':          dataset.nom_fichier,
            'nb_lignes':            dataset.nb_lignes,
            'nb_colonnes':          dataset.nb_colonnes,
            'has_date':             dataset.has_date,
            'statut':               dataset.statut,
            'rapport_nettoyage':    dataset.rapport_nettoyage,
            'colonnes':             colonnes_summary,
            'traitements_appliques': types_traitements,
        })


# ══════════════════════════════════════════════
# 10bis. COLONNES — GET /api/datasets/{id}/colonnes/
#    Endpoint léger consommé par Dev 2 et Dev 3
#    pour connaître les types de colonnes d'un dataset.
# ══════════════════════════════════════════════
class DatasetColonnesView(APIView):
    """
    Retourne uniquement la liste des colonnes et leurs types.
    Endpoint clé pour que service_analyse et service_visu sachent
    quelles colonnes sont quantitatives, qualitatives, datetime, etc.

    Réponse :
        [
          {"nom": "age",    "type": "numeric",  "nb_uniques": 72, "nb_manquantes": 3},
          {"nom": "region", "type": "text",     "nb_uniques": 14, "nb_manquantes": 0},
          ...
        ]
    """

    def get(self, request, pk):
        try:
            dataset = Dataset.objects.prefetch_related('colonnes').get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        colonnes = [
            {
                'nom':           c.nom,
                'type':          c.type_detecte,
                'nb_uniques':    c.nb_valeurs_uniques,
                'nb_manquantes': c.nb_valeurs_manquantes,
            }
            for c in dataset.colonnes.all()
        ]
        return ok(colonnes)


# ══════════════════════════════════════════════
# 10. SUPPRESSION — DELETE /api/datasets/{id}/delete/
# ══════════════════════════════════════════════
class DatasetDeleteView(APIView):
    """
    Supprime définitivement un dataset et toutes ses données associées
    (colonnes, logs de traitement, logs d'export).
    """

    def delete(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return err(f"Dataset {pk} introuvable.", status_code=404)

        nom = dataset.nom_fichier
        dataset.delete()  # CASCADE supprime aussi ColonneInfo, TraitementLog, ExportLog

        return ok(message=f"Dataset '{nom}' supprimé définitivement.")
