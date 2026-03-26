from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Dashboard, Widget


DATASET_ID = '00000000-0000-0000-0000-000000000001'

MOCK_DF_DATA = [
    {'region': 'Dakar',    'population': 3000, 'taux_alpha': 72.5},
    {'region': 'Thies',    'population': 2000, 'taux_alpha': 58.3},
    {'region': 'Diourbel', 'population': 1500, 'taux_alpha': 45.1},
    {'region': 'Kaolack',  'population': 1200, 'taux_alpha': 38.7},
]


class DashboardCRUDTests(APITestCase):

    def test_liste_vide(self):
        resp = self.client.get('/api/v1/dashboards/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_creer_dashboard(self):
        resp = self.client.post('/api/v1/dashboards/', {
            'dataset_id':  DATASET_ID,
            'dataset_nom': 'recensement_2024.csv',
            'titre':       'Mon dashboard test',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['titre'], 'Mon dashboard test')
        self.assertIn('share_token', resp.data)
        self.assertIn('share_url', resp.data)

    def test_creer_titre_vide(self):
        resp = self.client.post('/api/v1/dashboards/', {
            'dataset_id':  DATASET_ID,
            'dataset_nom': 'test.csv',
            'titre':       '   ',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detail_dashboard(self):
        d = Dashboard.objects.create(
            dataset_id=DATASET_ID,
            dataset_nom='test.csv',
            titre='Test',
        )
        resp = self.client.get(f'/api/v1/dashboards/{d.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['titre'], 'Test')
        self.assertIn('widgets', resp.data)

    def test_modifier_titre(self):
        d = Dashboard.objects.create(
            dataset_id=DATASET_ID, dataset_nom='test.csv', titre='Ancien'
        )
        resp = self.client.put(f'/api/v1/dashboards/{d.id}/', {
            'titre': 'Nouveau titre'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['titre'], 'Nouveau titre')

    def test_supprimer_dashboard(self):
        d = Dashboard.objects.create(
            dataset_id=DATASET_ID, dataset_nom='test.csv', titre='Test'
        )
        resp = self.client.delete(f'/api/v1/dashboards/{d.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dashboard.objects.filter(pk=d.id).exists())

    def test_dashboard_inexistant(self):
        resp = self.client.get('/api/v1/dashboards/00000000-0000-0000-0000-000000000099/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_share_token(self):
        d = Dashboard.objects.create(
            dataset_id=DATASET_ID, dataset_nom='test.csv', titre='Test'
        )
        resp = self.client.get(f'/api/v1/dashboards/share/{d.share_token}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['titre'], 'Test')

    def test_filtre_par_dataset(self):
        Dashboard.objects.create(
            dataset_id=DATASET_ID, dataset_nom='a.csv', titre='A'
        )
        Dashboard.objects.create(
            dataset_id='00000000-0000-0000-0000-000000000002',
            dataset_nom='b.csv', titre='B'
        )
        resp = self.client.get(f'/api/v1/dashboards/?dataset_id={DATASET_ID}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['titre'], 'A')


class WidgetTests(APITestCase):

    def setUp(self):
        self.dashboard = Dashboard.objects.create(
            dataset_id=DATASET_ID,
            dataset_nom='test.csv',
            titre='Dashboard test',
        )

    def test_ajouter_widget(self):
        resp = self.client.post(
            f'/api/v1/dashboards/{self.dashboard.id}/widgets/',
            {
                'type_widget': 'bar',
                'titre':       'Population par région',
                'variable_x':  'region',
                'variable_y':  'population',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['type_widget'], 'bar')
        self.assertEqual(self.dashboard.nb_widgets, 1)

    def test_type_widget_invalide(self):
        resp = self.client.post(
            f'/api/v1/dashboards/{self.dashboard.id}/widgets/',
            {'type_widget': 'radar', 'titre': 'Test',
             'variable_x': 'region'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supprimer_widget(self):
        w = Widget.objects.create(
            dashboard=self.dashboard,
            type_widget='bar',
            titre='Test',
            variable_x='region',
        )
        resp = self.client.delete(
            f'/api/v1/dashboards/{self.dashboard.id}/widgets/{w.id}/'
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Widget.objects.filter(pk=w.id).exists())

    def test_nb_widgets(self):
        Widget.objects.create(
            dashboard=self.dashboard, type_widget='bar',
            titre='W1', variable_x='region',
        )
        Widget.objects.create(
            dashboard=self.dashboard, type_widget='pie',
            titre='W2', variable_x='taux_alpha',
        )
        self.assertEqual(self.dashboard.nb_widgets, 2)


class GraphiquePreviewTests(APITestCase):

    @patch('dashboard_app.views.import_client')
    def test_preview_bar(self, mock_client):
        import pandas as pd
        mock_client.get_toutes_donnees_df.return_value = pd.DataFrame(MOCK_DF_DATA)

        resp = self.client.post('/api/v1/dashboards/graphique/', {
            'dataset_id':  DATASET_ID,
            'type_widget': 'bar',
            'variable_x':  'region',
            'variable_y':  'population',
            'titre':       'Population par région',
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['type'], 'bar')
        self.assertIn('data', resp.data)
        self.assertIn('labels', resp.data['data'])

    @patch('dashboard_app.views.import_client')
    def test_preview_pie(self, mock_client):
        import pandas as pd
        mock_client.get_toutes_donnees_df.return_value = pd.DataFrame(MOCK_DF_DATA)

        resp = self.client.post('/api/v1/dashboards/graphique/', {
            'dataset_id':  DATASET_ID,
            'type_widget': 'pie',
            'variable_x':  'region',
            'variable_y':  'population',
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['type'], 'pie')

    @patch('dashboard_app.views.import_client')
    def test_preview_service_indisponible(self, mock_client):
        from cartes_app.client_import import ImportClientError
        mock_client.get_toutes_donnees_df.side_effect = ImportClientError('hors ligne')

        resp = self.client.post('/api/v1/dashboards/graphique/', {
            'dataset_id':  DATASET_ID,
            'type_widget': 'bar',
            'variable_x':  'region',
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_preview_parametres_manquants(self):
        resp = self.client.post('/api/v1/dashboards/graphique/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)