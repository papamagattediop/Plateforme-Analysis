from django.urls import path, include
from django.http import HttpResponseRedirect
from cartes_app.urls import api_urlpatterns as cartes_api
from cartes_app.urls import html_urlpatterns as cartes_html
from dashboard_app.urls import api_urlpatterns as dashboard_api
from dashboard_app.urls import html_urlpatterns as dashboard_html

urlpatterns = [
    path('', lambda request: HttpResponseRedirect('/dashboard/')),
    path('api/v1/', include((cartes_api, 'cartes'))),
    path('api/v1/', include((dashboard_api, 'dashboard'))),
    *cartes_html,
    *dashboard_html,
]