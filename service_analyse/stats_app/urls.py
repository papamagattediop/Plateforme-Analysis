from django.urls import path
from . import views

urlpatterns = [
    # Proxy Dev 1
    path('datasets/', views.list_datasets),

    # Univarié quantitatif
    path('univariee/', views.univariee),
    path('ic/', views.ic),
    path('normalite/', views.normalite),
    path('histogramme/', views.histogramme),
    path('boxplot/', views.boxplot),

    # Univarié catégoriel
    path('frequences/', views.frequences),

    # Numérique × Numérique
    path('correlation/', views.correlation_bi),
    path('regression/', views.regression),
    path('regression-poly/', views.regression_poly),
    path('matrice-correlation/', views.matrice_correlation),
    path('scatter/', views.nuage_points),

    # Catégoriel × Catégoriel
    path('contingence/', views.contingence),

    # Catégoriel × Numérique
    path('stats-groupees/', views.stats_groupees),
    path('anova/', views.anova),
    path('ttest/', views.ttest),
    path('mann-whitney/', views.mann_whitney),
    path('kruskal/', views.kruskal),
    path('fisher-variance/', views.fisher_var),
    path('boxplot-groupe/', views.boxplot_groupe),

    path('suggest/', views.suggest),
]
