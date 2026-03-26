'''
Mock leger du service_analyse.
Permet a Dev 3 de travailler sans attendre Dev 2.

Lancement :
    python shared/mocks/analyse_mock.py
'''
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

MOCK_STATS_UNIVARIE = {
    'variable':   'age',
    'type':       'quantitative_discrete',
    'n':          1000,
    'moyenne':    32.4,
    'mediane':    30.0,
    'ecart_type': 12.1,
    'min': 18, 'max': 75,
    'q1': 24.0, 'q3': 42.0,
    'asymetrie': 0.42,
    'kurtosis':  -0.18,
}

MOCK_TEST_NORMALITE = {
    'statistique': 0.9821,
    'p_value':     0.0432,
    'decision':    'Non normal',
    'methode':     'shapiro',
    'alpha':       0.05,
}

MOCK_RESPONSES = {
    '/api/v1/stats/univarie/':   MOCK_STATS_UNIVARIE,
    '/api/v1/tests/normalite/':  MOCK_TEST_NORMALITE,
}

DEFAULT = {'detail': 'Mock: endpoint non configure'}


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = MOCK_RESPONSES.get(self.path, DEFAULT)
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f'  [MOCK analyse] {self.path} -> {args[1]}')


if __name__ == '__main__':
    print('Mock service_analyse -> http://localhost:8002')
    HTTPServer(('localhost', 8002), MockHandler).serve_forever()
