from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect

urlpatterns = [
    # ── HTML pages ──
    path('',        lambda req: HttpResponseRedirect('/stats/')),
    path('stats/',  TemplateView.as_view(template_name='stats_app/index.html'),      name='stats-home'),
    path('tests/',  TemplateView.as_view(template_name='tests_stat_app/index.html'), name='tests-home'),
    path('series/', TemplateView.as_view(template_name='series_app/index.html'),     name='series-home'),

    # ── API REST ──
    path('api/v1/', include('stats_app.urls')),
    path('api/v1/', include('tests_stat_app.urls')),
    path('api/v1/', include('series_app.urls')),
]
