"""
Client pour communiquer avec service_import (Dev 1).
Tant que Dev 1 n'a pas fini, on utilise les mocks.
"""
import requests
import pandas as pd
import numpy as np
from django.conf import settings


def get_datasets_list():
    url = f"{settings.SERVICE_IMPORT_URL}/api/v1/datasets/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return _mock_datasets_list()


def get_dataset_data(dataset_id, columns=None):
    url = f"{settings.SERVICE_IMPORT_URL}/api/v1/datasets/{dataset_id}/data/"
    params = {}
    if columns:
        params['colonnes'] = ','.join(columns)
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get('data', {})
        donnees = data.get('donnees', data.get('rows', []))
        cols = data.get('colonnes', data.get('columns', columns))
        if donnees and cols:
            return pd.DataFrame(donnees) if isinstance(donnees[0], dict) else pd.DataFrame(donnees, columns=cols)
        return pd.DataFrame(donnees)
    except Exception:
        return _mock_dataframe()


def get_dataset_columns(dataset_id):
    url = f"{settings.SERVICE_IMPORT_URL}/api/v1/datasets/{dataset_id}/colonnes/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return _mock_columns()


# ═══════════════ DONNÉES MOCK ═══════════════

def _mock_datasets_list():
    return [
        {'id': 1, 'name': 'recensement_2023.csv', 'rows': 5000, 'columns': 12},
        {'id': 2, 'name': 'population_regions.xlsx', 'rows': 1200, 'columns': 8},
    ]


def _mock_columns():
    return [
        {'name': 'region', 'type': 'text'},
        {'name': 'population', 'type': 'integer'},
        {'name': 'age_moyen', 'type': 'float'},
        {'name': 'taux_emploi', 'type': 'float'},
        {'name': 'annee', 'type': 'integer'},
        {'name': 'sexe', 'type': 'text'},
    ]


def _mock_dataframe():
    np.random.seed(42)
    n = 500
    regions = ['Ile-de-France', 'Auvergne', 'Bretagne', 'Occitanie', 'PACA']
    return pd.DataFrame({
        'region': np.random.choice(regions, n),
        'population': np.random.randint(10000, 500000, n),
        'age_moyen': np.random.normal(40, 12, n).round(1),
        'taux_emploi': np.random.uniform(0.45, 0.85, n).round(3),
        'annee': np.random.choice([2018, 2019, 2020, 2021, 2022, 2023], n),
        'sexe': np.random.choice(['M', 'F'], n),
    })