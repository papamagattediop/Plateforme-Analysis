"""
Vues cartes_app — API JSON + pages HTML Django templates.

API (préfixe /api/v1/) :
    POST /cartes/choropletre/
    POST /cartes/heatmap/
    POST /cartes/points/
    POST /cartes/comparaison/
    GET  /cartes/
    GET  /cartes/{id}/
    DELETE /cartes/{id}/
    GET  /cartes/geojson/
    GET  /cartes/share/{token}/

HTML :
    GET  /cartes/                      → page principale + formulaire
    GET  /cartes/{id}/view/            → carte sauvegardée plein écran
    GET  /cartes/share/{token}/        → page publique partagée
"""
import requests as http_requests

from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from django.shortcuts import render, get_object_or_404

from .models      import CarteGeneree, GeoJSONRegion
from .serializers import (
    CarteGenereeSerializer, CarteDetailSerializer,
    GeoJSONRegionSerializer,
    ChroropletrRequestSerializer,
    HeatmapRequestSerializer,
    PointsRequestSerializer,
    ComparaisonRequestSerializer,
)
from .engines.maps  import (
    generer_choropletre,
    generer_heatmap,
    generer_carte_points,
    generer_comparaison,
)
from .client_import import import_client, ImportClientError


# ─────────────────────────────────────────────────────────────────────────────
# API Views
# ─────────────────────────────────────────────────────────────────────────────

class ChroropletrView(APIView):
    """POST /api/v1/cartes/choropletre/"""

    def post(self, request):
        ser = ChroropletrRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data

        # 1. Récupérer les données depuis service_import
        try:
            colonnes = [d['colonne_geo'], d['variable']]
            if d.get('annee'):
                colonnes.append('annee')
            df = import_client.get_toutes_donnees_df(str(d['dataset_id']), colonnes)
        except ImportClientError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if df.empty:
            return Response({'error': 'Aucune donnée disponible'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # 2. Récupérer le GeoJSON
        try:
            geo_region = GeoJSONRegion.objects.get(nom=d['geojson_nom'])
        except GeoJSONRegion.DoesNotExist:
            return Response(
                {'error': f"GeoJSON '{d['geojson_nom']}' introuvable. Chargez-le via la commande charger_geojson."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 3. Générer la carte
        try:
            html = generer_choropletre(
                df=df,
                variable=d['variable'],
                colonne_geo=d['colonne_geo'],
                geojson_data=geo_region.geojson,
                cle_join=geo_region.cle_join,
                palette=d.get('palette', 'bleu'),
                titre=d.get('titre') or d['variable'],
                annee=d.get('annee'),
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        result = {'html_carte': html, 'type_carte': 'choropletre'}

        # 4. Sauvegarder si demandé
        if d.get('sauvegarder'):
            dataset_info = import_client.get_dataset(str(d['dataset_id']))
            carte = CarteGeneree.objects.create(
                dataset_id=str(d['dataset_id']),
                dataset_nom=dataset_info.get('nom', ''),
                type_carte='choropletre',
                variable=d['variable'],
                colonne_geo=d['colonne_geo'],
                annee=d.get('annee'),
                html_carte=html,
                config={
                    'palette':    d.get('palette', 'bleu'),
                    'geojson_nom': d['geojson_nom'],
                    'titre':      d.get('titre', ''),
                },
            )
            result['carte_id']    = str(carte.id)
            result['share_token'] = str(carte.share_token)
            result['share_url']   = carte.share_url

        return Response(result)


class HeatmapView(APIView):
    """POST /api/v1/cartes/heatmap/"""

    def post(self, request):
        ser = HeatmapRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data

        try:
            colonnes = [d['col_lat'], d['col_lon']]
            if d.get('col_intensite'):
                colonnes.append(d['col_intensite'])
            df = import_client.get_toutes_donnees_df(str(d['dataset_id']), colonnes)
        except ImportClientError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            html = generer_heatmap(
                df=df,
                col_lat=d['col_lat'],
                col_lon=d['col_lon'],
                col_intensite=d.get('col_intensite') or None,
                titre=d.get('titre'),
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        result = {'html_carte': html, 'type_carte': 'heatmap'}

        if d.get('sauvegarder'):
            dataset_info = import_client.get_dataset(str(d['dataset_id']))
            carte = CarteGeneree.objects.create(
                dataset_id=str(d['dataset_id']),
                dataset_nom=dataset_info.get('nom', ''),
                type_carte='heatmap',
                variable=d['col_lat'],
                html_carte=html,
                config={'col_lat': d['col_lat'], 'col_lon': d['col_lon']},
            )
            result['carte_id']    = str(carte.id)
            result['share_token'] = str(carte.share_token)
            result['share_url']   = carte.share_url

        return Response(result)


class PointsView(APIView):
    """POST /api/v1/cartes/points/"""

    def post(self, request):
        ser = PointsRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data

        try:
            colonnes = [d['col_lat'], d['col_lon']]
            if d.get('col_label'):
                colonnes.append(d['col_label'])
            df = import_client.get_toutes_donnees_df(str(d['dataset_id']), colonnes)
        except ImportClientError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            html = generer_carte_points(
                df=df,
                col_lat=d['col_lat'],
                col_lon=d['col_lon'],
                col_label=d.get('col_label') or None,
                col_couleur=d.get('col_couleur') or None,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        result = {'html_carte': html, 'type_carte': 'points'}

        if d.get('sauvegarder'):
            dataset_info = import_client.get_dataset(str(d['dataset_id']))
            carte = CarteGeneree.objects.create(
                dataset_id=str(d['dataset_id']),
                dataset_nom=dataset_info.get('nom', ''),
                type_carte='points',
                variable=d.get('col_label', d['col_lat']),
                html_carte=html,
                config={'col_lat': d['col_lat'], 'col_lon': d['col_lon']},
            )
            result['carte_id']    = str(carte.id)
            result['share_token'] = str(carte.share_token)
            result['share_url']   = carte.share_url

        return Response(result)


class ComparaisonView(APIView):
    """POST /api/v1/cartes/comparaison/"""

    def post(self, request):
        ser = ComparaisonRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data

        try:
            colonnes = [d['colonne_geo'], d['variable_gauche'], d['variable_droite']]
            df = import_client.get_toutes_donnees_df(str(d['dataset_id']), colonnes)
        except ImportClientError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            geo_region = GeoJSONRegion.objects.get(nom=d['geojson_nom'])
            result = generer_comparaison(
                df=df,
                variable_gauche=d['variable_gauche'],
                variable_droite=d['variable_droite'],
                colonne_geo=d['colonne_geo'],
                geojson_data=geo_region.geojson,
                cle_join=geo_region.cle_join,
                palette=d.get('palette', 'bleu'),
            )
        except GeoJSONRegion.DoesNotExist:
            return Response({'error': f"GeoJSON '{d['geojson_nom']}' introuvable"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(result)


class CarteListView(APIView):
    """GET /api/v1/cartes/"""

    def get(self, request):
        qs = CarteGeneree.objects.all()

        # Filtres optionnels
        dataset_id = request.query_params.get('dataset_id')
        type_carte = request.query_params.get('type_carte')
        if dataset_id:
            qs = qs.filter(dataset_id=dataset_id)
        if type_carte:
            qs = qs.filter(type_carte=type_carte)

        return Response(CarteGenereeSerializer(qs, many=True).data)


class CarteDetailView(APIView):
    """GET /api/v1/cartes/{id}/   DELETE /api/v1/cartes/{id}/"""

    def get(self, request, pk):
        carte = get_object_or_404(CarteGeneree, pk=pk)
        return Response(CarteDetailSerializer(carte).data)

    def delete(self, request, pk):
        carte = get_object_or_404(CarteGeneree, pk=pk)
        carte.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GeoJSONListView(APIView):
    """GET /api/v1/cartes/geojson/"""

    def get(self, request):
        geojsons = GeoJSONRegion.objects.all()
        return Response(GeoJSONRegionSerializer(geojsons, many=True).data)


class CarteShareAPIView(APIView):
    """GET /api/v1/cartes/share/{token}/"""

    def get(self, request, share_token):
        carte = get_object_or_404(CarteGeneree, share_token=share_token)
        return Response(CarteDetailSerializer(carte).data)


# ─────────────────────────────────────────────────────────────────────────────
# Template Views (HTML)
# ─────────────────────────────────────────────────────────────────────────────

def cartes_index(request):
    """
    GET /cartes/
    Page principale — formulaire de création + liste des cartes récentes.
    """
    dataset_id = request.GET.get('dataset_id')
    colonnes   = []
    dataset    = None
    geojsons   = GeoJSONRegion.objects.all()

    if dataset_id:
        try:
            dataset = import_client.get_dataset(dataset_id)
            data    = import_client.get_colonnes(dataset_id)
            colonnes = data.get('colonnes', [])
        except ImportClientError:
            pass

    return render(request, 'cartes/index.html', {
        'dataset':          dataset,
        'dataset_id':       dataset_id or '',
        'colonnes':         colonnes,
        'geojsons':         geojsons,
        'palettes':         list(PALETTES_LABELS.items()),
        'cartes_recentes':  CarteGeneree.objects.all()[:6],
    })


def carte_view(request, pk):
    """GET /cartes/{id}/view/  — Carte en plein écran."""
    carte = get_object_or_404(CarteGeneree, pk=pk)
    return render(request, 'cartes/carte_detail.html', {'carte': carte})


def carte_share_view(request, share_token):
    """GET /cartes/share/{token}/  — Page publique."""
    carte = get_object_or_404(CarteGeneree, share_token=share_token)
    return render(request, 'cartes/carte_share.html', {'carte': carte})


# Labels lisibles pour les templates
PALETTES_LABELS = {
    'bleu':   'Bleu',
    'vert':   'Vert',
    'rouge':  'Rouge',
    'orange': 'Orange',
    'violet': 'Violet',
}