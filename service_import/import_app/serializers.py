"""
serializers.py — Dev 1 · Sérialiseurs DRF
==========================================
Transforme les objets Django (Dataset, ColonneInfo, TraitementLog, ExportLog)
en JSON pour les réponses API.

Les serializers sont aussi utilisés pour valider les données entrantes
(ex: création d'un traitement manuel).
"""

from rest_framework import serializers
from .models import Dataset, ColonneInfo, TraitementLog, ExportLog


# ─────────────────────────────────────────────
# ColonneInfo — une colonne du dataset
# ─────────────────────────────────────────────
class ColonneInfoSerializer(serializers.ModelSerializer):
    """
    Sérialise une colonne avec son nom, son type détecté
    et ses statistiques rapides.
    """
    class Meta:
        model  = ColonneInfo
        fields = [
            'id',
            'nom',
            'type_detecte',
            'nb_valeurs_manquantes',
            'nb_valeurs_uniques',
            'exemple_valeurs',
        ]


# ─────────────────────────────────────────────
# TraitementLog — une entrée de l'historique
# ─────────────────────────────────────────────
class TraitementLogSerializer(serializers.ModelSerializer):
    """
    Sérialise un log de traitement.
    Le champ type_traitement_label expose le label lisible (ex: "Suppression des doublons").
    """
    # Champ calculé : label lisible du type de traitement
    type_traitement_label = serializers.CharField(
        source='get_type_traitement_display',
        read_only=True
    )

    class Meta:
        model  = TraitementLog
        fields = [
            'id',
            'type_traitement',
            'type_traitement_label',
            'description',
            'date_traitement',
            'details',
        ]
        # snapshot_avant n'est pas exposé dans la liste (trop volumineux)
        # il est accessible uniquement via l'endpoint de rollback


# ─────────────────────────────────────────────
# ExportLog — une entrée des exports
# ─────────────────────────────────────────────
class ExportLogSerializer(serializers.ModelSerializer):
    """Sérialise un log d'export."""

    format_label = serializers.CharField(
        source='get_format_export_display',
        read_only=True
    )

    class Meta:
        model  = ExportLog
        fields = ['id', 'format_export', 'format_label', 'date_export']


# ─────────────────────────────────────────────
# Dataset — liste (léger, sans données)
# ─────────────────────────────────────────────
class DatasetListSerializer(serializers.ModelSerializer):
    """
    Version légère du Dataset pour la liste /api/datasets/.
    N'inclut PAS les données JSON (trop volumineux pour une liste).
    """
    nb_traitements = serializers.IntegerField(
        source='traitements.count',
        read_only=True
    )
    statut_label = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )

    class Meta:
        model  = Dataset
        fields = [
            'id',
            'nom_fichier',
            'date_upload',
            'date_modif',
            'nb_lignes',
            'nb_colonnes',
            'has_date',
            'statut',
            'statut_label',
            'nb_traitements',
        ]


# ─────────────────────────────────────────────
# Dataset — détail complet (avec colonnes + logs)
# ─────────────────────────────────────────────
class DatasetDetailSerializer(serializers.ModelSerializer):
    """
    Version complète du Dataset pour /api/datasets/{id}/.
    Inclut les colonnes, le rapport de nettoyage et l'historique des traitements.
    N'inclut PAS les données brutes (accessible via /api/datasets/{id}/data/).
    """
    colonnes    = ColonneInfoSerializer(many=True, read_only=True)
    traitements = TraitementLogSerializer(many=True, read_only=True)
    exports     = ExportLogSerializer(many=True, read_only=True)
    statut_label = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )

    class Meta:
        model  = Dataset
        fields = [
            'id',
            'nom_fichier',
            'date_upload',
            'date_modif',
            'nb_lignes',
            'nb_colonnes',
            'has_date',
            'statut',
            'statut_label',
            'rapport_nettoyage',
            'colonnes',
            'traitements',
            'exports',
        ]
