"""
tests.py — Dev 1 · Tests unitaires et d'intégration
====================================================
Couvre tous les endpoints et les fonctions utilitaires.

Lancer les tests :
    python manage.py test import_app
    python manage.py test import_app --verbosity=2
"""

import io
import json
import pandas as pd

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from .models import Dataset, ColonneInfo, TraitementLog
from .utils import detect_types, nettoyer_dataframe, dataframe_to_json


# ═══════════════════════════════════════════
# TESTS DES UTILITAIRES (utils.py)
# ═══════════════════════════════════════════

class TestDetectTypes(TestCase):
    """Teste la détection automatique des types de colonnes."""

    def test_colonne_numerique(self):
        df = pd.DataFrame({'age': [23, 45, 67, 12]})
        types = detect_types(df)
        self.assertEqual(types['age'], 'numeric')

    def test_colonne_datetime(self):
        df = pd.DataFrame({'date': ['2023-01-01', '2023-06-15', '2024-03-20']})
        types = detect_types(df)
        self.assertEqual(types['date'], 'datetime')

    def test_colonne_categorielle(self):
        # Peu de valeurs uniques → catégoriel
        df = pd.DataFrame({'sexe': ['M', 'F', 'M', 'F', 'M', 'F', 'M']})
        types = detect_types(df)
        self.assertEqual(types['sexe'], 'categorical')

    def test_colonne_texte_libre(self):
        # Beaucoup de valeurs uniques → texte
        df = pd.DataFrame({'nom': [f'Personne_{i}' for i in range(200)]})
        types = detect_types(df)
        self.assertEqual(types['nom'], 'text')

    def test_has_date_flag(self):
        # Si au moins une colonne datetime → has_date = True
        df = pd.DataFrame({
            'age':  [23, 45],
            'date': ['2023-01-01', '2023-06-15']
        })
        types = detect_types(df)
        self.assertIn('datetime', types.values())


class TestNettoyage(TestCase):
    """Teste le nettoyage automatique du DataFrame."""

    def test_suppression_doublons(self):
        df = pd.DataFrame({'a': [1, 2, 2, 3], 'b': ['x', 'y', 'y', 'z']})
        df_clean, rapport = nettoyer_dataframe(df)
        self.assertEqual(len(df_clean), 3)
        op_doublons = next(o for o in rapport['operations'] if o['type'] == 'suppression_doublons')
        self.assertEqual(op_doublons['nb_supprimes'], 1)

    def test_suppression_lignes_vides(self):
        df = pd.DataFrame({'a': [1, None, 3], 'b': [None, None, 'z']})
        df_clean, rapport = nettoyer_dataframe(df)
        # La ligne [None, None] (entièrement vide) doit être supprimée
        self.assertEqual(len(df_clean), 2)

    def test_correction_decimales(self):
        df = pd.DataFrame({'valeur': ['3,14', '2,71', '1,41']})
        df_clean, rapport = nettoyer_dataframe(df)
        # Les valeurs doivent être converties en float
        self.assertTrue(pd.api.types.is_numeric_dtype(df_clean['valeur']))


# ═══════════════════════════════════════════
# TESTS DES ENDPOINTS API
# ═══════════════════════════════════════════

class TestUploadView(TestCase):
    """Teste l'endpoint POST /api/upload/."""

    def setUp(self):
        self.client = APIClient()

    def _creer_csv(self, contenu: str) -> SimpleUploadedFile:
        """Helper : crée un faux fichier CSV uploadé."""
        return SimpleUploadedFile(
            "test.csv",
            contenu.encode('utf-8'),
            content_type='text/csv'
        )

    def test_upload_csv_valide(self):
        csv = self._creer_csv("age,sexe,date_naissance\n23,M,1990-01-01\n45,F,1978-05-20")
        response = self.client.post('/api/upload/', {'fichier': csv}, format='multipart')
        self.assertEqual(response.status_code, 201)
        data = response.json()['data']
        self.assertIn('dataset_id', data)
        self.assertEqual(data['nb_colonnes'], 3)
        # 'date_naissance' doit être détecté comme datetime → has_date = True
        self.assertTrue(data['has_date'])

    def test_upload_sans_fichier(self):
        response = self.client.post('/api/upload/', {}, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_upload_format_invalide(self):
        fichier = SimpleUploadedFile("test.pdf", b"contenu", content_type='application/pdf')
        response = self.client.post('/api/upload/', {'fichier': fichier}, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_dataset_cree_en_base(self):
        csv = self._creer_csv("nom,age\nAlice,30\nBob,25")
        self.client.post('/api/upload/', {'fichier': csv}, format='multipart')
        self.assertEqual(Dataset.objects.count(), 1)
        self.assertEqual(ColonneInfo.objects.count(), 2)
        self.assertEqual(TraitementLog.objects.filter(type_traitement='import').count(), 1)


class TestDatasetDetailView(TestCase):
    """Teste GET /api/datasets/{id}/."""

    def setUp(self):
        self.client = APIClient()
        # Créer un dataset de test directement en base
        self.dataset = Dataset.objects.create(
            nom_fichier='test.csv',
            nb_lignes=100,
            nb_colonnes=3,
            has_date=True,
            statut='traite',
            donnees_json=[{'age': 23, 'sexe': 'M'}],
        )

    def test_detail_existant(self):
        response = self.client.get(f'/api/datasets/{self.dataset.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['nom_fichier'], 'test.csv')

    def test_detail_inexistant(self):
        response = self.client.get('/api/datasets/9999/')
        self.assertEqual(response.status_code, 404)


class TestDatasetExportView(TestCase):
    """Teste GET /api/datasets/{id}/export/{format}/."""

    def setUp(self):
        self.client = APIClient()
        self.dataset = Dataset.objects.create(
            nom_fichier='export_test.csv',
            nb_lignes=2,
            nb_colonnes=2,
            statut='traite',
            donnees_json=[{'age': 23, 'ville': 'Dakar'}, {'age': 45, 'ville': 'Abidjan'}],
        )

    def test_export_csv(self):
        response = self.client.get(f'/api/datasets/{self.dataset.id}/export/csv/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])

    def test_export_xlsx(self):
        response = self.client.get(f'/api/datasets/{self.dataset.id}/export/xlsx/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_export_json(self):
        response = self.client.get(f'/api/datasets/{self.dataset.id}/export/json/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])

    def test_format_invalide(self):
        response = self.client.get(f'/api/datasets/{self.dataset.id}/export/pdf/')
        self.assertEqual(response.status_code, 400)


class TestRollbackView(TestCase):
    """Teste le rollback d'un traitement."""

    def setUp(self):
        self.client = APIClient()
        self.dataset = Dataset.objects.create(
            nom_fichier='rollback_test.csv',
            statut='traite',
            donnees_json=[{'a': 1}, {'a': 2}],
        )
        # Simuler un traitement avec snapshot
        TraitementLog.objects.create(
            dataset=self.dataset,
            type_traitement='suppression_doublons',
            description='Test',
            snapshot_avant=[{'a': 1}, {'a': 2}, {'a': 2}],  # Données avant
        )

    def test_rollback_restaure_donnees(self):
        response = self.client.post(f'/api/datasets/{self.dataset.id}/rollback/')
        self.assertEqual(response.status_code, 200)
        self.dataset.refresh_from_db()
        # Les données doivent être restaurées (3 lignes)
        self.assertEqual(self.dataset.nb_lignes, 3)
        # Le log doit être supprimé
        self.assertEqual(TraitementLog.objects.filter(dataset=self.dataset).count(), 0)
