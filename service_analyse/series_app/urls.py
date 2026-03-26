from django.urls import path
from . import views

urlpatterns = [
    path('stationarity/', views.stationarity),
    path('arima/', views.arima),
    path('prophet/', views.prophet_forecast),
]