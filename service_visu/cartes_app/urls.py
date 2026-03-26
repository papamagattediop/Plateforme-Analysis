from django.urls import path
from . import views

app_name = 'cartes_app'

# ── Endpoints API JSON ─────────────────────────────────────────────────────────
api_urlpatterns = [
    path('cartes/choropletre/',              views.ChroropletrView.as_view(),  name='choropletre'),
    path('cartes/heatmap/',                  views.HeatmapView.as_view(),      name='heatmap'),
    path('cartes/points/',                   views.PointsView.as_view(),       name='points'),
    path('cartes/comparaison/',              views.ComparaisonView.as_view(),  name='comparaison'),
    path('cartes/',                          views.CarteListView.as_view(),    name='liste'),
    path('cartes/<uuid:pk>/',               views.CarteDetailView.as_view(),  name='detail'),
    path('cartes/geojson/',                  views.GeoJSONListView.as_view(),  name='geojson'),
    path('cartes/share/<uuid:share_token>/', views.CarteShareAPIView.as_view(), name='share-api'),
]

# ── Pages HTML ─────────────────────────────────────────────────────────────────
html_urlpatterns = [
    path('cartes/',                           views.cartes_index,      name='index'),
    path('cartes/<uuid:pk>/view/',            views.carte_view,        name='vue'),
    path('cartes/share/<uuid:share_token>/',  views.carte_share_view,  name='share'),
]