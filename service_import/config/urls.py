from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect

urlpatterns = [
    # ── HTML pages ──
    path('',       lambda req: HttpResponseRedirect('/import/')),
    path('import/', TemplateView.as_view(template_name='import_app/index.html'), name='import-home'),

    # ── API REST ──
    path('api/v1/', include('import_app.urls')),
]
