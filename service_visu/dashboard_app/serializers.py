from rest_framework import serializers
from .models import Dashboard, Widget


# ── Serializers de lecture ────────────────────────────────────

class WidgetSerializer(serializers.ModelSerializer):
    type_widget_label = serializers.CharField(
        source='get_type_widget_display', read_only=True
    )

    class Meta:
        model  = Widget
        fields = [
            'id', 'type_widget', 'type_widget_label',
            'titre', 'variable_x', 'variable_y',
            'filtres', 'config', 'position',
        ]


class DashboardSerializer(serializers.ModelSerializer):
    widgets   = WidgetSerializer(many=True, read_only=True)
    share_url = serializers.ReadOnlyField()
    nb_widgets = serializers.ReadOnlyField()

    class Meta:
        model  = Dashboard
        fields = [
            'id', 'dataset_id', 'dataset_nom', 'titre',
            'share_token', 'share_url', 'nb_widgets',
            'created_at', 'updated_at',
            'widgets',
        ]


class DashboardListSerializer(serializers.ModelSerializer):
    """Version allégée sans les widgets — pour la liste."""
    nb_widgets = serializers.ReadOnlyField()

    class Meta:
        model  = Dashboard
        fields = [
            'id', 'dataset_id', 'dataset_nom', 'titre',
            'share_token', 'nb_widgets', 'updated_at',
        ]


# ── Serializers d'écriture ────────────────────────────────────

class DashboardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Dashboard
        fields = ['dataset_id', 'dataset_nom', 'titre']

    def validate_titre(self, value):
        if not value.strip():
            raise serializers.ValidationError("Le titre ne peut pas être vide.")
        return value.strip()


class DashboardUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Dashboard
        fields = ['titre']


class WidgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Widget
        fields = [
            'type_widget', 'titre',
            'variable_x', 'variable_y',
            'filtres', 'config', 'position',
        ]

    def validate_type_widget(self, value):
        types_valides = [t[0] for t in Widget.TYPE_CHOICES]
        if value not in types_valides:
            raise serializers.ValidationError(
                f"Type invalide. Choisir parmi : {types_valides}"
            )
        return value


# ── Serializers de requête ────────────────────────────────────

class GraphiqueRequestSerializer(serializers.Serializer):
    """Paramètres pour générer la config d'un graphique."""
    dataset_id  = serializers.UUIDField()
    type_widget = serializers.ChoiceField(choices=[t[0] for t in Widget.TYPE_CHOICES])
    variable_x  = serializers.CharField(max_length=255)
    variable_y  = serializers.CharField(max_length=255, required=False, allow_blank=True)
    titre       = serializers.CharField(max_length=255, required=False, allow_blank=True)
    filtres     = serializers.DictField(required=False, default=dict)