import uuid
from django.db import models


class GeoJSONRegion(models.Model):
    """
    Découpage géographique stocké en base.
    Chargé une fois via : python manage.py charger_geojson
    Ex : régions du Sénégal, pays d'Afrique de l'Ouest...
    """
    nom        = models.CharField(max_length=255, unique=True)
    label      = models.CharField(max_length=255)
    niveau     = models.CharField(max_length=50)
    cle_join   = models.CharField(max_length=100)
    geojson    = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'geojson_regions'

    def __str__(self):
        return f'{self.label} ({self.niveau})'


class CarteGeneree(models.Model):
    """
    Carte Folium générée et mise en cache.
    share_token permet le partage public sans compte.
    """
    TYPE_CHOICES = [
        ('choropletre', 'Choroplèthe'),
        ('heatmap',     'Carte de chaleur'),
        ('points',      'Carte de points'),
        ('comparaison', 'Comparaison 2 variables'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset_id  = models.CharField(max_length=255)
    dataset_nom = models.CharField(max_length=255)
    type_carte  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    variable    = models.CharField(max_length=255)
    colonne_geo = models.CharField(max_length=255, blank=True)
    annee       = models.CharField(max_length=10, blank=True, null=True)
    config      = models.JSONField(default=dict)
    html_carte  = models.TextField(blank=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cartes_generees'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.type_carte} — {self.variable} ({self.dataset_nom})'

    @property
    def share_url(self):
        return f'/cartes/share/{self.share_token}/'
