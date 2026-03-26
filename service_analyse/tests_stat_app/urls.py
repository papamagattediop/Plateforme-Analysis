from django.urls import path
from . import views

app_name = 'tests_stat_app'

urlpatterns = [
    path('tests/normalite/',    views.NormaliteView.as_view(),    name='normalite'),
    path('tests/comparaison/',  views.ComparaisonView.as_view(),  name='comparaison'),
    path('tests/independance/', views.IndependanceView.as_view(), name='independance'),
    path('tests/selectionner/', views.SelecteurView.as_view(),    name='selecteur'),
]
