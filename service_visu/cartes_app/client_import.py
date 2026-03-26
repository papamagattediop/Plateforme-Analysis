"""
Client HTTP pour consommer l'API du service_import (Dev 1).
Pendant le développement, utiliser le mock : python shared/mocks/import_mock.py
"""
import os
import requests
import pandas as pd

SERVICE_IMPORT_URL = os.environ.get('SERVICE_IMPORT_URL', 'http://localhost:8001')
TIMEOUT = 15


class ImportClientError(Exception):
    pass


class ServiceImportClient:

    def get_dataset(self, dataset_id: str) -> dict:
        """Métadonnées d'un dataset."""
        try:
            r = requests.get(
                f'{SERVICE_IMPORT_URL}/api/v1/datasets/{dataset_id}/',
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise ImportClientError(f'service_import inaccessible : {e}')

    def get_colonnes(self, dataset_id: str) -> dict:
        """
        Types de colonnes détectés — endpoint clé pour savoir
        quelles colonnes sont quantitatives, qualitatives, datetime...
        """
        try:
            r = requests.get(
                f'{SERVICE_IMPORT_URL}/api/v1/datasets/{dataset_id}/colonnes/',
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise ImportClientError(f'service_import inaccessible : {e}')

    def get_donnees_page(
        self,
        dataset_id: str,
        colonnes: list = None,
        page: int = 1,
        per_page: int = 1000,
    ) -> dict:
        """Données paginées d'un dataset."""
        params = {'page': page, 'per_page': per_page}
        if colonnes:
            params['colonnes'] = ','.join(colonnes)
        try:
            r = requests.get(
                f'{SERVICE_IMPORT_URL}/api/v1/datasets/{dataset_id}/data/',
                params=params,
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise ImportClientError(f'service_import inaccessible : {e}')

    def get_toutes_donnees_df(
        self,
        dataset_id: str,
        colonnes: list = None,
    ) -> pd.DataFrame:
        """
        Récupère TOUTES les données et retourne un DataFrame pandas.
        Gère la pagination automatiquement.
        """
        toutes = []
        page = 1

        while True:
            result = self.get_donnees_page(dataset_id, colonnes, page, per_page=1000)
            toutes.extend(result.get('donnees', []))

            if page >= result.get('nb_pages', 1):
                break
            page += 1

        if not toutes:
            return pd.DataFrame()

        return pd.DataFrame(toutes)

    def get_preview(self, dataset_id: str) -> dict:
        """Aperçu des 20 premières lignes."""
        try:
            r = requests.get(
                f'{SERVICE_IMPORT_URL}/api/v1/datasets/{dataset_id}/preview/',
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise ImportClientError(f'service_import inaccessible : {e}')

    def get_par_token(self, share_token: str) -> dict:
        """Accès par lien de partage."""
        try:
            r = requests.get(
                f'{SERVICE_IMPORT_URL}/api/v1/datasets/share/{share_token}/',
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise ImportClientError(f'service_import inaccessible : {e}')


# Instance singleton
import_client = ServiceImportClient()