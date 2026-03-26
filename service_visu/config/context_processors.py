"""
Injecte les URLs inter-services dans tous les templates.
"""
from django.conf import settings


def service_urls(request):
    return {
        'SERVICE_IMPORT_URL':  getattr(settings, 'SERVICE_IMPORT_URL',  'http://localhost:8001'),
        'SERVICE_ANALYSE_URL': getattr(settings, 'SERVICE_ANALYSE_URL', 'http://localhost:8002'),
        'SERVICE_VISU_URL':    getattr(settings, 'SERVICE_VISU_URL',    'http://localhost:8003'),
    }
