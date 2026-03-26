from django.shortcuts import render

# Create your views here.

# stats_app/views.py
from .selector import suggest_test
from rest_framework.decorators import api_view
from rest_framework.response import Response
from analyse.api_client import get_dataset_data, get_datasets_list
from .utils.stats import (
    # Univarié quantitatif
    stats_descriptives, confidence_interval, distribution_fit,
    histogram_data, boxplot_data,
    # Univarié catégoriel
    freq_table,
    # Numérique × Numérique
    correlation_deux_variables, regression_lineaire,
    regression_polynomiale, correlation_matrix, scatter_data,
    # Catégoriel × Catégoriel
    contingency_table,
    # Catégoriel × Numérique
    stats_par_groupe, test_anova, test_ttest, test_mann_whitney,
    test_kruskal, test_fisher_variance, boxplot_par_groupe,
)


# ── Proxy Dev 1 ──

@api_view(['GET'])
def list_datasets(request):
    return Response(get_datasets_list())


# ══════════ UNIVARIÉ QUANTITATIF ══════════

@api_view(['POST'])
def univariee(request):
    """POST {"dataset_id": 1, "column": "age_moyen"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(stats_descriptives(df, request.data['column']))


@api_view(['POST'])
def ic(request):
    """POST {"dataset_id": 1, "column": "age_moyen", "confidence": 0.95}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(confidence_interval(
        df, request.data['column'], request.data.get('confidence', 0.95)
    ))


@api_view(['POST'])
def normalite(request):
    """POST {"dataset_id": 1, "column": "age_moyen"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(distribution_fit(df, request.data['column']))


@api_view(['POST'])
def histogramme(request):
    """POST {"dataset_id": 1, "column": "age_moyen", "bins": 20}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(histogram_data(
        df, request.data['column'], request.data.get('bins', 20)
    ))


@api_view(['POST'])
def boxplot(request):
    """POST {"dataset_id": 1, "column": "age_moyen"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(boxplot_data(df, request.data['column']))


# ══════════ UNIVARIÉ CATÉGORIEL ══════════

@api_view(['POST'])
def frequences(request):
    """POST {"dataset_id": 1, "column": "region"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(freq_table(df, request.data['column']))


# ══════════ NUMÉRIQUE × NUMÉRIQUE ══════════

@api_view(['POST'])
def correlation_bi(request):
    """POST {"dataset_id": 1, "col_x": "age_moyen", "col_y": "taux_emploi"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(correlation_deux_variables(
        df, request.data['col_x'], request.data['col_y']
    ))


@api_view(['POST'])
def regression(request):
    """POST {"dataset_id": 1, "col_x": "age_moyen", "col_y": "taux_emploi"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(regression_lineaire(
        df, request.data['col_x'], request.data['col_y']
    ))


@api_view(['POST'])
def regression_poly(request):
    """POST {"dataset_id": 1, "col_x": "age_moyen", "col_y": "taux_emploi", "degree": 2}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(regression_polynomiale(
        df, request.data['col_x'], request.data['col_y'],
        request.data.get('degree', 2)
    ))


@api_view(['POST'])
def matrice_correlation(request):
    """POST {"dataset_id": 1, "columns": ["population", "age_moyen", "taux_emploi"]}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(correlation_matrix(df, request.data.get('columns', [])))


@api_view(['POST'])
def nuage_points(request):
    """POST {"dataset_id": 1, "col_x": "age_moyen", "col_y": "taux_emploi"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(scatter_data(df, request.data['col_x'], request.data['col_y']))


# ══════════ CATÉGORIEL × CATÉGORIEL ══════════

@api_view(['POST'])
def contingence(request):
    """POST {"dataset_id": 1, "col1": "region", "col2": "sexe"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(contingency_table(df, request.data['col1'], request.data['col2']))


# ══════════ CATÉGORIEL × NUMÉRIQUE ══════════

@api_view(['POST'])
def stats_groupees(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "region"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(stats_par_groupe(
        df, request.data['col_numeric'], request.data['col_group']
    ))


@api_view(['POST'])
def anova(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "region"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(test_anova(df, request.data['col_numeric'], request.data['col_group']))


@api_view(['POST'])
def ttest(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "sexe"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(test_ttest(df, request.data['col_numeric'], request.data['col_group']))


@api_view(['POST'])
def mann_whitney(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "sexe"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(test_mann_whitney(
        df, request.data['col_numeric'], request.data['col_group']
    ))


@api_view(['POST'])
def kruskal(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "region"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(test_kruskal(df, request.data['col_numeric'], request.data['col_group']))


@api_view(['POST'])
def fisher_var(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "sexe"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(test_fisher_variance(
        df, request.data['col_numeric'], request.data['col_group']
    ))


@api_view(['POST'])
def boxplot_groupe(request):
    """POST {"dataset_id": 1, "col_numeric": "age_moyen", "col_group": "region"}"""
    df = get_dataset_data(request.data.get('dataset_id'))
    return Response(boxplot_par_groupe(
        df, request.data['col_numeric'], request.data['col_group']
    ))



@api_view(['POST'])
def suggest(request):
    """POST {"col_x_type": "numeric", "col_y_type": "categorical", "nb_groups": 2, "normal": true}"""
    return Response(suggest_test(
        request.data.get('col_x_type'),
        request.data.get('col_y_type'),
        request.data.get('nb_groups'),
        request.data.get('normal'),
    ))