from rest_framework import serializers


class NormaliteRequestSerializer(serializers.Serializer):
    dataset_id = serializers.CharField()
    colonne    = serializers.CharField()
    methode    = serializers.ChoiceField(
        choices=['shapiro', 'kstest', 'anderson'], default='shapiro'
    )


class ComparaisonRequestSerializer(serializers.Serializer):
    dataset_id    = serializers.CharField()
    colonne       = serializers.CharField()
    col_groupe    = serializers.CharField()
    methode       = serializers.ChoiceField(
        choices=['ttest', 'anova', 'mann_whitney', 'kruskal'], default='ttest'
    )
    apparie       = serializers.BooleanField(default=False)


class IndependanceRequestSerializer(serializers.Serializer):
    dataset_id = serializers.CharField()
    col_var1   = serializers.CharField(required=False, allow_blank=True, default='')
    col_var2   = serializers.CharField(required=False, allow_blank=True, default='')
    col_x      = serializers.CharField(required=False, allow_blank=True, default='')
    col_y      = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, data):
        # Accepter col_x/col_y comme alias de col_var1/col_var2
        if not data.get('col_var1') and data.get('col_x'):
            data['col_var1'] = data['col_x']
        if not data.get('col_var2') and data.get('col_y'):
            data['col_var2'] = data['col_y']
        if not data.get('col_var1') or not data.get('col_var2'):
            raise serializers.ValidationError("col_var1 et col_var2 (ou col_x et col_y) sont requis.")
        return data


class SelecteurRequestSerializer(serializers.Serializer):
    """Auto-sélection : accepte dataset_id + colonne et dérive les paramètres."""
    dataset_id  = serializers.CharField()
    colonne     = serializers.CharField()
    col_groupe  = serializers.CharField(required=False, allow_blank=True, default='')
