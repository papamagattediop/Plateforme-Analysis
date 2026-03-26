from django.urls import path
from . import views

app_name = 'dashboard_app'

# ── Endpoints API JSON ─────────────────────────────────────────
api_urlpatterns = [
    path('dashboards/',
         views.DashboardListView.as_view(),       name='liste'),
    path('dashboards/<uuid:pk>/',
         views.DashboardDetailView.as_view(),     name='detail'),
    path('dashboards/<uuid:pk>/widgets/',
         views.WidgetListView.as_view(),          name='widgets'),
    path('dashboards/<uuid:pk>/widgets/<int:widget_pk>/',
         views.WidgetDetailView.as_view(),        name='widget-detail'),
    path('dashboards/graphique/',
         views.GraphiquePreviewView.as_view(),    name='graphique-preview'),
    path('dashboards/share/<uuid:share_token>/',
         views.DashboardShareAPIView.as_view(),   name='share-api'),
    path('dashboards/<uuid:pk>/export/pdf/',
         views.ExportPDFView.as_view(),           name='export-pdf'),
]

# ── Pages HTML ─────────────────────────────────────────────────
html_urlpatterns = [
    path('dashboard/',
         views.dashboard_index,                  name='index'),
    path('dashboard/<uuid:pk>/',
         views.dashboard_view,                   name='vue'),
    path('dashboard/share/<uuid:share_token>/',
         views.dashboard_share_view,             name='share'),
]