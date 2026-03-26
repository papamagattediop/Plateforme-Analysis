from rest_framework import serializers


class SeriesRequestSerializer(serializers.Serializer):
    dataset_id  = serializers.UUIDField()
    col_date    = serializers.CharField()
    col_valeur  = serializers.CharField()
    periode     = serializers.IntegerField(required=False, min_value=2)


class PrevisionRequestSerializer(SeriesRequestSerializer):
    horizon  = serializers.IntegerField(default=12, min_value=1, max_value=60)
    methode  = serializers.ChoiceField(choices=['arima', 'prophet'], default='arima')
