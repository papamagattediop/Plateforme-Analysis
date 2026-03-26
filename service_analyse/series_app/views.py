from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd

from analyse.api_client import get_dataset_data
from .utils.series import test_adf, test_kpss_stationarity, fit_arima, fit_prophet


@api_view(['POST'])
def stationarity(request):
    df = get_dataset_data(request.data.get('dataset_id'))
    col = request.data['column']
    return Response({
        'adf': test_adf(df[col]),
        'kpss': test_kpss_stationarity(df[col]),
    })


@api_view(['POST'])
def arima(request):
    df = get_dataset_data(request.data.get('dataset_id'))
    order = tuple(request.data.get('order', [1, 1, 1]))
    periods = request.data.get('periods', 5)
    return Response(fit_arima(df[request.data['column']], order, periods))


@api_view(['POST'])
def prophet_forecast(request):
    df = get_dataset_data(request.data.get('dataset_id'))
    col_date = request.data['col_date']
    col_value = request.data['col_value']
    periods = request.data.get('periods', 5)

    df_ts = pd.DataFrame({
        'ds': pd.to_datetime(df[col_date], format='%Y'),
        'y': pd.to_numeric(df[col_value], errors='coerce'),
    }).dropna().groupby('ds')['y'].sum().reset_index()

    return Response(fit_prophet(df_ts, periods))