from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CarteGeneree, GeoJSONRegion


GEOJSON_SIMPLE = {
    'type': 'FeatureCollection',
    'features': [
        {
            'type': 'Feature',
            'properties': {'nom_region': 'Dakar'},
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[
                    [-17.5, 14.5],
                    [-17.0, 14.5],
                    [-17.0, 15.0],
                    [-17.5, 15.0],
                    [-17.5, 14.5],
                ]],
            },
        }
    ],
}

MOCK_DF_DATA = [
    {'region': 'Dakar',    'taux_alpha': 72.5},
    {'region': 'Thies',    'taux_alpha': 58.3},
    {'region': 'Diourbel', 'taux_alpha': 45.1},
]


class GeoJSONRegionTests(APITestCase):

    def setUp(self):
        self.geo = GeoJSONRegion.objects.create(
            nom='test_regions',
            label='Régions test',
            niveau='region',
            cle_join='nom_region',
            geojson=GEOJSON_SIMPLE,
        )

    def test_liste_geojson(self):
        resp = self.client.get('/api/v1/cartes/geojson/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['nom'], 'test_regions')

    def test_geojson_label(self):
        self.assertEqual(str(self.geo), 'Régions test (region)')


class CarteListTests(APITestCase):

    def test_liste_vide(self):
        resp = self.client.get('/api/v1/cartes/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_liste_avec_filtre_type(self):
        CarteGeneree.objects.create(
            dataset_id='00000000-0000-0000-0000-000000000001',
            dataset_nom='test.csv',
            type_carte='choropletre',
            variable='taux_alpha',
        )
        CarteGeneree.objects.create(
            dataset_id='00000000-0000-0000-0000-000000000001',
            dataset_nom='test.csv',
            type_carte='heatmap',
            variable='lat',
        )
        resp = self.client.get('/api/v1/cartes/?type_carte=choropletre')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)


class CarteDetailTests(APITestCase):

    def setUp(self):
        self.carte = CarteGeneree.objects.create(
            dataset_id='00000000-0000-0000-0000-000000000001',
            dataset_nom='test.csv',
            type_carte='choropletre',
            variable='taux_alpha',
            html_carte='<html>carte</html>',
        )

    def test_detail_carte(self):
        resp = self.client.get(f'/api/v1/cartes/{self.carte.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('html_carte', resp.data)

    def test_supprimer_carte(self):
        resp = self.client.delete(f'/api/v1/cartes/{self.carte.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CarteGeneree.objects.filter(pk=self.carte.id).exists())

    def test_share_token(self):
        resp = self.client.get(f'/api/v1/cartes/share/{self.carte.share_token}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['variable'], 'taux_alpha')

    def test_carte_inexistante(self):
        resp = self.client.get('/api/v1/cartes/00000000-0000-0000-0000-000000000099/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ChroropletrViewTests(APITestCase):

    def setUp(self):
        GeoJSONRegion.objects.create(
            nom='senegal_regions',
            label='Régions du Sénégal',
            niveau='region',
            cle_join='region',
            geojson=GEOJSON_SIMPLE,
        )

    # On mocke AUSSI generer_choropletre pour ne pas avoir besoin de Folium
    @patch('cartes_app.views.generer_choropletre')
    @patch('cartes_app.views.import_client')
    def test_choropletre_valide(self, mock_client, mock_generer):
        import pandas as pd
        mock_client.get_toutes_donnees_df.return_value = pd.DataFrame(MOCK_DF_DATA)
        mock_client.get_dataset.return_value = {'nom': 'test.csv'}
        mock_generer.return_value = '<html>carte folium mockee</html>'

        resp = self.client.post('/api/v1/cartes/choropletre/', {
            'dataset_id':  '00000000-0000-0000-0000-000000000001',
            'variable':    'taux_alpha',
            'colonne_geo': 'region',
            'geojson_nom': 'senegal_regions',
            'palette':     'bleu',
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('html_carte', resp.data)
        self.assertEqual(resp.data['type_carte'], 'choropletre')

    # GeoJSON 'inexistant' n'est pas en base → 404
    @patch('cartes_app.views.import_client')
    def test_choropletre_geojson_manquant(self, mock_client):
        import pandas as pd
        mock_client.get_toutes_donnees_df.return_value = pd.DataFrame(MOCK_DF_DATA)

        resp = self.client.post('/api/v1/cartes/choropletre/', {
            'dataset_id':  '00000000-0000-0000-0000-000000000001',
            'variable':    'taux_alpha',
            'colonne_geo': 'region',
            'geojson_nom': 'inexistant',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_choropletre_parametres_manquants(self):
        resp = self.client.post('/api/v1/cartes/choropletre/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)