from django.contrib import admin
from .models import Dataset, ColonneInfo, TraitementLog, ExportLog


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display   = ['nom_fichier', 'nb_lignes', 'nb_colonnes', 'statut', 'date_upload']
    list_filter    = ['statut', 'has_date']
    search_fields  = ['nom_fichier']
    readonly_fields = ['id', 'date_upload', 'date_modif']


@admin.register(ColonneInfo)
class ColonneInfoAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'dataset', 'type_detecte', 'nb_valeurs_manquantes']
    list_filter   = ['type_detecte']
    search_fields = ['nom', 'dataset__nom_fichier']


@admin.register(TraitementLog)
class TraitementLogAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'type_traitement', 'date_traitement']
    list_filter  = ['type_traitement']
    readonly_fields = ['date_traitement']


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'format_export', 'date_export']
    readonly_fields = ['date_export']
