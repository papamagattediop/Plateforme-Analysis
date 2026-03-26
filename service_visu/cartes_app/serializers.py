from rest_framework import serializers
from .models import CarteGeneree, GeoJSONRegion


# ── Serializers de lecture ────────────────────────────────────────────────────

class GeoJSONRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = GeoJSONRegion
        fields = ['id', 'nom', 'label', 'niveau', 'cle_join']


class CarteGenereeSerializer(serializers.ModelSerializer):
    share_url = serializers.ReadOnlyField()

    class Meta:
        model  = CarteGeneree
        fields = [
            'id', 'dataset_id', 'dataset_nom',
            'type_carte', 'variable', 'colonne_geo', 'annee',
            'config', 'share_token', 'share_url', 'created_at',
        ]


class CarteDetailSerializer(CarteGenereeSerializer):
    """Version complète avec le HTML de la carte."""
    class Meta(CarteGenereeSerializer.Meta):
        fields = CarteGenereeSerializer.Meta.fields + ['html_carte']


# ── Serializers de requête ────────────────────────────────────────────────────

class ChroropletrRequestSerializer(serializers.Serializer):
    dataset_id  = serializers.UUIDField()
    variable    = serializers.CharField(max_length=255)
    colonne_geo = serializers.CharField(max_length=255)
    geojson_nom = serializers.CharField(max_length=255)
    palette     = serializers.ChoiceField(
        choices=['bleu', 'vert', 'rouge', 'orange', 'violet'],
        default='bleu',
    )
    annee       = serializers.CharField(
        max_length=10, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    titre       = serializers.CharField(
        max_length=255, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    sauvegarder = serializers.BooleanField(default=False)


class HeatmapRequestSerializer(serializers.Serializer):
    dataset_id    = serializers.UUIDField()
    col_lat       = serializers.CharField(max_length=255)
    col_lon       = serializers.CharField(max_length=255)
    col_intensite = serializers.CharField(
        max_length=255, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    titre         = serializers.CharField(
        max_length=255, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    sauvegarder   = serializers.BooleanField(default=False)


class PointsRequestSerializer(serializers.Serializer):
    dataset_id  = serializers.UUIDField()
    col_lat     = serializers.CharField(max_length=255)
    col_lon     = serializers.CharField(max_length=255)
    col_label   = serializers.CharField(
        max_length=255, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    col_couleur = serializers.CharField(
        max_length=255, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    titre       = serializers.CharField(
        max_length=255, required=False,
        allow_blank=True, allow_null=True, default=None,
    )
    sauvegarder = serializers.BooleanField(default=False)


class ComparaisonRequestSerializer(serializers.Serializer):
    dataset_id      = serializers.UUIDField()
    variable_gauche = serializers.CharField(max_length=255)
    variable_droite = serializers.CharField(max_length=255)
    colonne_geo     = serializers.CharField(max_length=255)
    geojson_nom     = serializers.CharField(max_length=255)
    palette         = serializers.ChoiceField(
        choices=['bleu', 'vert', 'rouge', 'orange', 'violet'],
        default='bleu',
    )
    annee           = serializers.CharField(
        max_length=10, required=False,
        allow_blank=True, allow_null=True, default=None,
    )

    def validate(self, data):
        """Vérifier que les deux variables sont différentes."""
        if data.get('variable_gauche') == data.get('variable_droite'):
            raise serializers.ValidationError(
                'Les deux variables doivent être différentes.'
            )
        return data