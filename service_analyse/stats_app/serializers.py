from rest_framework import serializers


class UnivariéRequestSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()
    colonne    = serializers.CharField()
    type_var   = serializers.ChoiceField(choices=[
        'quantitative_continue', 'quantitative_discrete',
        'qualitative_nominale', 'qualitative_ordinale',
    ])


class BivarieRequestSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()
    colonne_x  = serializers.CharField()
    colonne_y  = serializers.CharField()


class DemographieRequestSerializer(serializers.Serializer):
    dataset_id  = serializers.UUIDField()
    col_age     = serializers.CharField()
    col_sexe    = serializers.CharField()
    col_region  = serializers.CharField(required=False)
