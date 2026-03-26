"""
tasks.py — Dev 1 · Tâches Celery asynchrones
=============================================
Les tâches Celery permettent de traiter des fichiers volumineux
en arrière-plan sans bloquer la réponse HTTP.

Utilisation typique :
    1. L'upload crée le Dataset avec statut='en_attente'
    2. La vue retourne immédiatement un dataset_id
    3. Celery traite le fichier en arrière-plan
    4. Le statut passe à 'traite' quand c'est fini

Configuration requise dans settings.py :
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
"""

from celery import shared_task
from django.utils import timezone

from .models import Dataset, ColonneInfo, TraitementLog
from .utils import lire_fichier, nettoyer_dataframe, detect_types, stats_colonne, dataframe_to_json


@shared_task(bind=True, max_retries=3)
def traiter_fichier_async(self, dataset_id: int):
    """
    Tâche Celery : traite un fichier volumineux en arrière-plan.
    Appelée après l'upload si le fichier dépasse une certaine taille.

    Args:
        dataset_id: ID du Dataset à traiter (doit exister en base)

    Retourne:
        dict avec le résultat du traitement
    """
    try:
        # ── Récupérer le dataset ──
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.statut = 'en_traitement'
        dataset.save()

        # ── Relire le fichier depuis le stockage ──
        with dataset.fichier.open('rb') as f:
            df = lire_fichier(f)

        # ── Nettoyage ──
        df, rapport = nettoyer_dataframe(df)

        # ── Détection des types ──
        types = detect_types(df)
        has_date = 'datetime' in types.values()

        # ── Mettre à jour le dataset ──
        dataset.nb_lignes         = len(df)
        dataset.nb_colonnes       = len(df.columns)
        dataset.has_date          = has_date
        dataset.rapport_nettoyage = rapport
        dataset.donnees_json      = dataframe_to_json(df.copy())
        dataset.statut            = 'traite'
        dataset.save()

        # ── Créer les ColonneInfo (supprimer les anciennes si re-traitement) ──
        dataset.colonnes.all().delete()
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

        # ── Log du traitement ──
        TraitementLog.objects.create(
            dataset         = dataset,
            type_traitement = 'import',
            description     = f"Import asynchrone du fichier '{dataset.nom_fichier}'",
            details         = rapport,
        )

        return {
            'status':     'success',
            'dataset_id': dataset_id,
            'nb_lignes':  dataset.nb_lignes,
            'has_date':   has_date,
        }

    except Dataset.DoesNotExist:
        # Dataset supprimé entre l'upload et l'exécution de la tâche
        return {'status': 'error', 'message': f"Dataset {dataset_id} introuvable."}

    except Exception as exc:
        # ── Marquer le dataset en erreur ──
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            dataset.statut = 'erreur'
            dataset.rapport_nettoyage = {'erreur': str(exc)}
            dataset.save()
        except Exception:
            pass

        # ── Retry automatique (max 3 fois) ──
        raise self.retry(exc=exc, countdown=10)  # Réessayer après 10 secondes
