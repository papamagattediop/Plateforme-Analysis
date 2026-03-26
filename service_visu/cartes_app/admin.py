from django.contrib import admin
from .models import CarteGeneree, GeoJSONRegion


@admin.register(GeoJSONRegion)
class GeoJSONRegionAdmin(admin.ModelAdmin):
    list_display  = ['label', 'niveau', 'nom', 'cle_join', 'created_at']
    search_fields = ['nom', 'label']
    readonly_fields = ['created_at']


@admin.register(CarteGeneree)
class CarteGenereeAdmin(admin.ModelAdmin):
    list_display    = ['dataset_nom', 'type_carte', 'variable', 'colonne_geo', 'annee', 'created_at']
    list_filter     = ['type_carte']
    search_fields   = ['dataset_nom', 'variable']
    readonly_fields = ['id', 'share_token', 'created_at', 'updated_at']
    exclude         = ['html_carte']   # trop volumineux pour l'admin