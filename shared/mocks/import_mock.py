"""
Mock du service_import.
Lancement : python shared/mocks/import_mock.py
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

MOCK_DATASET = {
    'id':             '00000000-0000-0000-0000-000000000001',
    'nom':            'recensement_2024.csv',
    'nb_lignes':      1000,
    'nb_colonnes':    5,
    'has_date_column': False,
    'colonne_date':   None,
    'statut':         'ready',
}

MOCK_COLONNES = {
    'dataset_id':      '00000000-0000-0000-0000-000000000001',
    'nb_variables':    5,
    'has_date_column': False,
    'colonne_date':    None,
    'colonnes': [
        {'nom': 'region',     'type_detecte': 'qualitative_nominale',  'position': 0},
        {'nom': 'age',        'type_detecte': 'quantitative_discrete', 'position': 1},
        {'nom': 'sexe',       'type_detecte': 'qualitative_nominale',  'position': 2},
        {'nom': 'taux_alpha', 'type_detecte': 'quantitative_continue', 'position': 3},
        {'nom': 'population', 'type_detecte': 'quantitative_continue', 'position': 4},
    ],
}

# Données simulées par région du Sénégal (NAME_1 = clé du GeoJSON GADM)
MOCK_DATA = {
    'nb_total': 14,
    'nb_pages': 1,
    'page':     1,
    'donnees': [
        {'region': 'Dakar',         'age': 28, 'sexe': 'H', 'taux_alpha': 78.5, 'population': 3732000},
        {'region': 'Thiès',         'age': 31, 'sexe': 'F', 'taux_alpha': 58.3, 'population': 1875000},
        {'region': 'Diourbel',      'age': 29, 'sexe': 'H', 'taux_alpha': 42.1, 'population': 1685000},
        {'region': 'Kaolack',       'age': 33, 'sexe': 'F', 'taux_alpha': 45.7, 'population': 1054000},
        {'region': 'Saint-Louis',   'age': 35, 'sexe': 'H', 'taux_alpha': 52.4, 'population': 994000},
        {'region': 'Ziguinchor',    'age': 27, 'sexe': 'F', 'taux_alpha': 55.2, 'population': 594000},
        {'region': 'Fatick',        'age': 32, 'sexe': 'H', 'taux_alpha': 38.9, 'population': 756000},
        {'region': 'Kolda',         'age': 26, 'sexe': 'F', 'taux_alpha': 33.6, 'population': 662000},
        {'region': 'Tambacounda',   'age': 30, 'sexe': 'H', 'taux_alpha': 36.8, 'population': 728000},
        {'region': 'Louga',         'age': 34, 'sexe': 'F', 'taux_alpha': 44.1, 'population': 874000},
        {'region': 'Matam',         'age': 29, 'sexe': 'H', 'taux_alpha': 31.2, 'population': 562000},
        {'region': 'Kaffrine',      'age': 31, 'sexe': 'F', 'taux_alpha': 29.8, 'population': 543000},
        {'region': 'Kédougou',      'age': 25, 'sexe': 'H', 'taux_alpha': 28.4, 'population': 179000},
        {'region': 'Sédhiou',       'age': 28, 'sexe': 'F', 'taux_alpha': 32.1, 'population': 452000},
    ],
}

DEFAULT = {'detail': 'Mock: endpoint non configuré'}

ROUTES = {
    '/api/v1/datasets/':                                              [MOCK_DATASET],
    '/api/v1/datasets/00000000-0000-0000-0000-000000000001/':         MOCK_DATASET,
    '/api/v1/datasets/00000000-0000-0000-0000-000000000001/colonnes/': MOCK_COLONNES,
    '/api/v1/datasets/00000000-0000-0000-0000-000000000001/data/':    MOCK_DATA,
    '/api/v1/datasets/00000000-0000-0000-0000-000000000001/preview/': MOCK_DATA,
}


class MockHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Ignorer les query params (?page=1...)
        path = self.path.split('?')[0]
        data = ROUTES.get(path, DEFAULT)
        self._respond(200, data)

    def do_POST(self):
        body = json.dumps({
            'id': '00000000-0000-0000-0000-000000000001',
            'statut': 'ready',
        }).encode()
        self._respond(201, None, body)

    def _respond(self, code, data=None, raw=None):
        body = raw or json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f'  [MOCK] {self.path.split("?")[0]} → {args[1]}')


if __name__ == '__main__':
    print('='*45)
    print('  Mock service_import → http://localhost:8001')
    print('  Dataset : recensement_2024.csv (14 régions)')
    print('='*45)
    HTTPServer(('localhost', 8001), MockHandler).serve_forever()