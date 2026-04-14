import uuid
from django.db import models


class Dashboard(models.Model):
    """
    Dashboard sauvegardé par l'utilisateur.
    Contient plusieurs widgets (visualisations).
    share_token permet le partage public sans compte.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset_id  = models.CharField(max_length=255)
    dataset_nom = models.CharField(max_length=255)
    titre       = models.CharField(max_length=255, default='Mon dashboard')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboards'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.titre} ({self.dataset_nom})'

    @property
    def share_url(self):
        return f'/dashboard/share/{self.share_token}/'

    @property
    def nb_widgets(self):
        return self.widgets.count()


class Widget(models.Model):
    """
    Visualisation individuelle dans un dashboard.
    Chaque widget = un graphique avec sa configuration.
    """
    TYPE_CHOICES = [
        ('bar',       'Barres'),
        ('line',      'Lignes'),
        ('pie',       'Camembert'),
        ('scatter',   'Nuage de points'),
        ('histogram', 'Histogramme'),
        ('heatmap',   'Heatmap'),
        ('pyramid',   'Pyramide des âges'),
        ('table',     'Tableau'),
        ('carte',     'Carte Folium'),
    ]

    dashboard   = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name='widgets'
    )
    type_widget = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre       = models.CharField(max_length=255)
    variable_x  = models.CharField(max_length=255)
    variable_y  = models.CharField(max_length=255, blank=True)
    filtres     = models.JSONField(default=dict, blank=True)
    config      = models.JSONField(default=dict, blank=True)
    position    = models.IntegerField(default=0)

    class Meta:
        db_table = 'widgets'
        ordering = ['position']

    def __str__(self):
        return f'{self.get_type_widget_display()} — {self.titre}'