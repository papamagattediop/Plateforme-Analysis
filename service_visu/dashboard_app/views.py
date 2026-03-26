"""
Vues dashboard_app — API JSON + pages HTML.

API :
    GET    /api/v1/dashboards/                    liste
    POST   /api/v1/dashboards/                    créer
    GET    /api/v1/dashboards/{id}/               détail
    PUT    /api/v1/dashboards/{id}/               modifier titre
    DELETE /api/v1/dashboards/{id}/               supprimer
    POST   /api/v1/dashboards/{id}/widgets/       ajouter widget
    DELETE /api/v1/dashboards/{id}/widgets/{wid}/ supprimer widget
    POST   /api/v1/dashboards/graphique/          prévisualiser graphique
    GET    /api/v1/dashboards/share/{token}/      accès public
    GET    /api/v1/dashboards/{id}/export/pdf/    export PDF

HTML :
    GET  /dashboard/                 builder
    GET  /dashboard/{id}/           dashboard sauvegardé
    GET  /dashboard/share/{token}/  page publique
"""
from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from django.shortcuts import render, get_object_or_404

from .models      import Dashboard, Widget
from .serializers import (
    DashboardSerializer, DashboardListSerializer,
    DashboardCreateSerializer, DashboardUpdateSerializer,
    WidgetSerializer, WidgetCreateSerializer,
    GraphiqueRequestSerializer,
)
from .engines.builder import generer_config_graphique
from .engines.export  import exporter_dashboard_pdf

from cartes_app.client_import import import_client, ImportClientError


# ─────────────────────────────────────────────────────────────
# API — Dashboards
# ─────────────────────────────────────────────────────────────

class DashboardListView(APIView):
    """GET /api/v1/dashboards/   POST /api/v1/dashboards/"""

    def get(self, request):
        dashboards = Dashboard.objects.all()
        dataset_id = request.query_params.get('dataset_id')
        if dataset_id:
            dashboards = dashboards.filter(dataset_id=dataset_id)
        return Response(DashboardListSerializer(dashboards, many=True).data)

    def post(self, request):
        ser = DashboardCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        dashboard = ser.save()
        return Response(
            DashboardSerializer(dashboard).data,
            status=status.HTTP_201_CREATED,
        )


class DashboardDetailView(APIView):
    """GET / PUT / DELETE /api/v1/dashboards/{id}/"""

    def get(self, request, pk):
        dashboard = get_object_or_404(Dashboard, pk=pk)
        return Response(DashboardSerializer(dashboard).data)

    def put(self, request, pk):
        dashboard = get_object_or_404(Dashboard, pk=pk)
        ser = DashboardUpdateSerializer(dashboard, data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ser.save()
        return Response(DashboardSerializer(dashboard).data)

    def delete(self, request, pk):
        dashboard = get_object_or_404(Dashboard, pk=pk)
        dashboard.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardShareAPIView(APIView):
    """GET /api/v1/dashboards/share/{token}/"""

    def get(self, request, share_token):
        dashboard = get_object_or_404(Dashboard, share_token=share_token)
        return Response(DashboardSerializer(dashboard).data)


# ─────────────────────────────────────────────────────────────
# API — Widgets
# ─────────────────────────────────────────────────────────────

class WidgetListView(APIView):
    """POST /api/v1/dashboards/{id}/widgets/"""

    def post(self, request, pk):
        dashboard = get_object_or_404(Dashboard, pk=pk)
        ser = WidgetCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        # Position automatique à la fin
        derniere_position = dashboard.widgets.count()
        widget = ser.save(
            dashboard=dashboard,
            position=request.data.get('position', derniere_position),
        )
        return Response(
            WidgetSerializer(widget).data,
            status=status.HTTP_201_CREATED,
        )


class WidgetDetailView(APIView):
    """DELETE /api/v1/dashboards/{id}/widgets/{wid}/"""

    def delete(self, request, pk, widget_pk):
        widget = get_object_or_404(Widget, pk=widget_pk, dashboard__pk=pk)
        widget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk, widget_pk):
        widget = get_object_or_404(Widget, pk=widget_pk, dashboard__pk=pk)
        ser = WidgetCreateSerializer(widget, data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ser.save()
        return Response(WidgetSerializer(widget).data)


# ─────────────────────────────────────────────────────────────
# API — Prévisualisation graphique
# ─────────────────────────────────────────────────────────────

class GraphiquePreviewView(APIView):
    """
    POST /api/v1/dashboards/graphique/
    Génère la config Chart.js pour un graphique sans le sauvegarder.
    Utilisé par le builder côté frontend pour la prévisualisation.
    """

    def post(self, request):
        ser = GraphiqueRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data

        # Récupérer les données depuis service_import
        try:
            colonnes = [d['variable_x']]
            if d.get('variable_y'):
                colonnes.append(d['variable_y'])
            df = import_client.get_toutes_donnees_df(
                str(d['dataset_id']), colonnes
            )
        except ImportClientError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if df.empty:
            return Response(
                {'error': 'Aucune donnée disponible pour ce dataset'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Générer la config Chart.js
        config = generer_config_graphique(
            df=df,
            type_widget=d['type_widget'],
            variable_x=d['variable_x'],
            variable_y=d.get('variable_y') or None,
            titre=d.get('titre', ''),
            filtres=d.get('filtres', {}),
        )

        if 'erreur' in config:
            return Response(
                {'error': config['erreur']},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(config)


# ─────────────────────────────────────────────────────────────
# API — Export PDF
# ─────────────────────────────────────────────────────────────

class ExportPDFView(APIView):
    """GET /api/v1/dashboards/{id}/export/pdf/"""

    def get(self, request, pk):
        dashboard = get_object_or_404(Dashboard, pk=pk)

        try:
            df = import_client.get_toutes_donnees_df(str(dashboard.dataset_id))
        except ImportClientError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Générer les configs pour chaque widget
        widgets_data = []
        for widget in dashboard.widgets.all():
            config = generer_config_graphique(
                df=df.copy(),
                type_widget=widget.type_widget,
                variable_x=widget.variable_x,
                variable_y=widget.variable_y or None,
                titre=widget.titre,
                filtres=widget.filtres,
            )
            widgets_data.append({'widget': widget, 'config': config})

        try:
            return exporter_dashboard_pdf(dashboard, widgets_data)
        except ImportError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# ─────────────────────────────────────────────────────────────
# Template Views (HTML)
# ─────────────────────────────────────────────────────────────

def dashboard_index(request):
    """
    GET /dashboard/
    Page principale — builder + liste des dashboards.
    """
    dataset_id = request.GET.get('dataset_id') or request.COOKIES.get('active_dataset_id')
    colonnes   = []
    dataset    = None

    if dataset_id:
        try:
            dataset  = import_client.get_dataset(dataset_id)
            colonnes = import_client.get_colonnes(dataset_id)
        except ImportClientError:
            pass

    dashboards_recents = Dashboard.objects.all()[:5]

    return render(request, 'dashboard/index.html', {
        'dataset':            dataset,
        'dataset_id':         dataset_id or '',
        'colonnes':           colonnes,
        'dashboards_recents': dashboards_recents,
        'types_graphiques':   Widget.TYPE_CHOICES,
    })


def dashboard_view(request, pk):
    """GET /dashboard/{id}/ — Dashboard complet."""
    dashboard = get_object_or_404(Dashboard, pk=pk)
    return render(request, 'dashboard/dashboard_detail.html', {
        'dashboard': dashboard,
        'widgets':   dashboard.widgets.all(),
    })


def dashboard_share_view(request, share_token):
    """GET /dashboard/share/{token}/ — Page publique."""
    dashboard = get_object_or_404(Dashboard, share_token=share_token)
    return render(request, 'dashboard/dashboard_share.html', {
        'dashboard': dashboard,
        'widgets':   dashboard.widgets.all(),
    })