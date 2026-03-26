"""
models.py — Dev 1 · Data Ingestion
====================================
Définit les tables PostgreSQL du service d'import :
  - Dataset      : métadonnées du fichier uploadé
  - ColonneInfo  : chaque colonne détectée avec son type
  - TraitementLog: historique de chaque opération effectuée sur un dataset
  - ExportLog    : trace des exports effectués
"""

from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────
# 1. Dataset — représente un fichier uploadé
# ─────────────────────────────────────────────
class Dataset(models.Model):

    # Statuts possibles du traitement
    STATUT_CHOICES = [
        ('en_attente',    'En attente de traitement'),
        ('en_traitement', 'En cours de traitement'),
        ('traite',        'Traité avec succès'),
        ('erreur',        'Erreur lors du traitement'),
    ]

    # Informations de base du fichier
    nom_fichier  = models.CharField(max_length=255, help_text="Nom original du fichier uploadé")
    fichier      = models.FileField(upload_to='uploads/', help_text="Fichier stocké sur le serveur")
    date_upload  = models.DateTimeField(auto_now_add=True, help_text="Date/heure d'upload automatique")
    date_modif   = models.DateTimeField(auto_now=True, help_text="Dernière modification")

    # Dimensions du dataset
    nb_lignes    = models.IntegerField(default=0, help_text="Nombre de lignes après nettoyage")
    nb_colonnes  = models.IntegerField(default=0, help_text="Nombre de colonnes détectées")

    # Flag critique pour Dev 2 : active le module M5 Séries temporelles
    has_date     = models.BooleanField(default=False, help_text="True si une colonne datetime est détectée → active M5")

    # Statut global du traitement
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    # Rapport de nettoyage stocké en JSON brut
    rapport_nettoyage = models.JSONField(default=dict, blank=True,
                                         help_text="Rapport JSON : doublons, lignes vides, encodage, etc.")

    # Snapshot des données nettoyées (JSON) pour export rapide
    # Attention : pour de gros volumes, utiliser plutôt un fichier parquet
    donnees_json = models.JSONField(default=list, blank=True,
                                    help_text="Données nettoyées stockées en JSON pour export/consultation")

    class Meta:
        db_table = 'datasets'
        ordering = ['-date_upload']
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"

    def __str__(self):
        return f"{self.nom_fichier} ({self.statut})"


# ─────────────────────────────────────────────
# 2. ColonneInfo — une colonne du dataset
# ─────────────────────────────────────────────
class ColonneInfo(models.Model):

    TYPE_CHOICES = [
        ('numeric',     'Numérique'),
        ('categorical', 'Catégoriel'),
        ('datetime',    'Date / Heure'),
        ('text',        'Texte libre'),
        ('boolean',     'Booléen'),
        ('inconnu',     'Type inconnu'),
    ]

    # Liaison au dataset parent
    dataset      = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                     related_name='colonnes',
                                     help_text="Dataset auquel appartient cette colonne")

    nom          = models.CharField(max_length=255, help_text="Nom de la colonne dans le fichier")
    type_detecte = models.CharField(max_length=20, choices=TYPE_CHOICES,
                                    help_text="Type détecté automatiquement par utils.py")

    # Statistiques rapides pré-calculées (évite de recalculer côté Dev 2)
    nb_valeurs_manquantes = models.IntegerField(default=0)
    nb_valeurs_uniques    = models.IntegerField(default=0)
    exemple_valeurs       = models.JSONField(default=list, blank=True,
                                             help_text="3-5 exemples de valeurs pour aperçu")

    class Meta:
        db_table = 'colonnes_info'
        ordering = ['nom']
        verbose_name = "Colonne"
        verbose_name_plural = "Colonnes"
        unique_together = ('dataset', 'nom')

    def __str__(self):
        return f"{self.dataset.nom_fichier} → {self.nom} [{self.type_detecte}]"


# ─────────────────────────────────────────────
# 3. TraitementLog — historique des modifications
#    Chaque action sur un dataset est tracée ici
# ─────────────────────────────────────────────
class TraitementLog(models.Model):

    TYPE_TRAITEMENT = [
        ('import',              'Import initial'),
        ('suppression_doublons','Suppression des doublons'),
        ('suppression_vides',   'Suppression lignes vides'),
        ('correction_types',    'Correction des types'),
        ('renommage_colonne',   'Renommage de colonne'),
        ('suppression_colonne', 'Suppression de colonne'),
        ('remplacement_valeur', 'Remplacement de valeur'),
        ('normalisation',       'Normalisation'),
        ('encodage',            'Correction encodage'),
        ('autre',               'Autre traitement'),
    ]

    dataset        = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                       related_name='traitements',
                                       help_text="Dataset concerné")

    type_traitement = models.CharField(max_length=30, choices=TYPE_TRAITEMENT)
    description     = models.TextField(help_text="Description lisible du traitement effectué")
    date_traitement = models.DateTimeField(default=timezone.now)

    # Détails techniques (avant/après, nb lignes affectées, etc.)
    details         = models.JSONField(default=dict, blank=True,
                                       help_text="Détails JSON : ex. {'avant': 1200, 'apres': 1185, 'diff': 15}")

    # Snapshot des données AVANT modification (pour permettre l'annulation)
    snapshot_avant  = models.JSONField(default=list, blank=True,
                                       help_text="Snapshot JSON des données avant cette modification")

    class Meta:
        db_table = 'traitements_log'
        ordering = ['-date_traitement']
        verbose_name = "Log de traitement"
        verbose_name_plural = "Logs de traitements"

    def __str__(self):
        return f"[{self.date_traitement:%Y-%m-%d %H:%M}] {self.dataset.nom_fichier} — {self.get_type_traitement_display()}"


# ─────────────────────────────────────────────
# 4. ExportLog — trace des exports effectués
# ─────────────────────────────────────────────
class ExportLog(models.Model):

    FORMAT_CHOICES = [
        ('csv',  'CSV'),
        ('xlsx', 'Excel (.xlsx)'),
        ('json', 'JSON'),
    ]

    dataset      = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                     related_name='exports',
                                     help_text="Dataset exporté")

    format_export = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    date_export   = models.DateTimeField(auto_now_add=True)
    chemin_fichier = models.CharField(max_length=500, blank=True,
                                      help_text="Chemin du fichier exporté sur le serveur")

    class Meta:
        db_table = 'exports_log'
        ordering = ['-date_export']
        verbose_name = "Export"
        verbose_name_plural = "Exports"

    def __str__(self):
        return f"Export {self.format_export.upper()} — {self.dataset.nom_fichier} ({self.date_export:%Y-%m-%d})"
