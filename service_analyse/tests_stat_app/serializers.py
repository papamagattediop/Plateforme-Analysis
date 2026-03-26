from rest_framework import serializers


class NormaliteRequestSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()
    colonne    = serializers.CharField()
    methode    = serializers.ChoiceField(
        choices=['shapiro', 'kstest', 'anderson'], default='shapiro'
    )


class ComparaisonRequestSerializer(serializers.Serializer):
    dataset_id    = serializers.UUIDField()
    colonne       = serializers.CharField()
    col_groupe    = serializers.CharField()
    methode       = serializers.ChoiceField(
        choices=['ttest', 'anova', 'mann_whitney', 'kruskal'], default='ttest'
    )
    apparie       = serializers.BooleanField(default=False)


class IndependanceRequestSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()
    col_var1   = serializers.CharField()
    col_var2   = serializers.CharField()


class SelecteurRequestSerializer(serializers.Serializer):
    type_variable = serializers.ChoiceField(choices=['quantitative', 'qualitative'])
    nb_groupes    = serializers.IntegerField(default=2, min_value=1)
    apparie       = serializers.BooleanField(default=False)
    normal        = serializers.BooleanField(default=True)
