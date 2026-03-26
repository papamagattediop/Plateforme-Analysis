from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd

from analyse.api_client import get_dataset_data
from .utils.series import test_adf, test_kpss_stationarity, fit_arima, fit_prophet


@api_view(['POST'])
def stationarity(request):
    df  = get_dataset_data(request.data.get('dataset_id'))
    col = request.data.get('colonne_valeur') or request.data.get('column', '')
    return Response({
        'adf':  test_adf(df[col]),
        'kpss': test_kpss_stationarity(df[col]),
    })


@api_view(['POST'])
def arima(request):
    df  = get_dataset_data(request.data.get('dataset_id'))
    col = request.data.get('colonne_valeur') or request.data.get('column', '')

    # Accepter order comme tuple OU comme p/d/q séparés
    order = request.data.get('order') or (
        int(request.data.get('p', 1)),
        int(request.data.get('d', 1)),
        int(request.data.get('q', 1)),
    )
    order   = tuple(order)
    periods = int(request.data.get('horizons') or request.data.get('periods', 5))

    return Response(fit_arima(df[col], order, periods))


@api_view(['POST'])
def prophet_forecast(request):
    df        = get_dataset_data(request.data.get('dataset_id'))
    col_date  = request.data.get('colonne_date')  or request.data.get('col_date', '')
    col_value = request.data.get('colonne_valeur') or request.data.get('col_value', '')
    periods   = int(request.data.get('horizons') or request.data.get('periods', 5))

    # Auto-détection du format date (supporte YYYY-MM-DD, YYYY-MM, YYYY, etc.)
    df_ts = pd.DataFrame({
        'ds': pd.to_datetime(df[col_date], errors='coerce'),
        'y':  pd.to_numeric(df[col_value], errors='coerce'),
    }).dropna().groupby('ds')['y'].sum().reset_index()

    return Response(fit_prophet(df_ts, periods))