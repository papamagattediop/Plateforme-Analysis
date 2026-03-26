"""
tests_stat_app/views.py — Dev 2
================================
Endpoints de tests statistiques inférentiels.

  POST /api/v1/tests/normalite/    → Shapiro-Wilk / KS / Anderson-Darling
  POST /api/v1/tests/comparaison/  → t-test, ANOVA, Mann-Whitney, Kruskal
  POST /api/v1/tests/independance/ → Chi2 d'indépendance
  POST /api/v1/tests/selectionner/ → Assistant sélection automatique du test
"""

import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    NormaliteRequestSerializer,
    ComparaisonRequestSerializer,
    IndependanceRequestSerializer,
    SelecteurRequestSerializer,
)
from .engines.tests import (
    test_normalite,
    test_student,
    test_anova,
    test_chi2,
    test_mann_whitney,
)
from .selector import selectionner_test

# Client vers service_import (avec fallback mock)
try:
    from analyse.api_client import get_dataset_data
except ImportError:
    def get_dataset_data(dataset_id, columns=None):
        import numpy as np
        n = 200
        return pd.DataFrame({
            'age':    np.random.normal(35, 12, n),
            'region': np.random.choice(['Dakar', 'Thiès', 'Ziguinchor', 'Saint-Louis'], n),
            'revenu': np.random.normal(250000, 80000, n),
            'sexe':   np.random.choice(['M', 'F'], n),
        })


def _err(msg, details=None, code=400):
    return Response({'status': 'error', 'message': msg, 'details': details}, status=code)


def _ok(data, message=''):
    return Response({'status': 'success', 'message': message, 'data': data})


# ══════════════════════════════════════════════════
# 1. NORMALITÉ — POST /api/v1/tests/normalite/
# ══════════════════════════════════════════════════
class NormaliteView(APIView):
    """
    Teste si une variable quantitative suit une loi normale.
    Méthodes disponibles : shapiro (défaut), kstest, anderson.
    """

    def post(self, request):
        ser = NormaliteRequestSerializer(data=request.data)
        if not ser.is_valid():
            return _err("Paramètres invalides.", details=ser.errors)

        dataset_id = str(ser.validated_data['dataset_id'])
        colonne    = ser.validated_data['colonne']
        methode    = ser.validated_data['methode']

        try:
            df = get_dataset_data(dataset_id)
        except Exception as e:
            return _err(f"Impossible de récupérer les données : {e}", code=502)

        if colonne not in df.columns:
            return _err(f"Colonne '{colonne}' introuvable dans le dataset.")

        try:
            resultat = test_normalite(df[colonne], methode=methode)
        except ValueError as e:
            return _err(str(e))
        except Exception as e:
            return _err(f"Erreur lors du test de normalité : {e}", code=500)

        return _ok({
            'dataset_id': dataset_id,
            'colonne':    colonne,
            'n':          int(df[colonne].dropna().shape[0]),
            'resultat':   resultat,
        })


# ══════════════════════════════════════════════════
# 2. COMPARAISON — POST /api/v1/tests/comparaison/
# ══════════════════════════════════════════════════
class ComparaisonView(APIView):
    """
    Compare les distributions d'une variable quantitative entre groupes.
    Méthodes : ttest (défaut), anova, mann_whitney, kruskal.
    """

    def post(self, request):
        ser = ComparaisonRequestSerializer(data=request.data)
        if not ser.is_valid():
            return _err("Paramètres invalides.", details=ser.errors)

        dataset_id = str(ser.validated_data['dataset_id'])
        colonne    = ser.validated_data['colonne']
        col_groupe = ser.validated_data['col_groupe']
        methode    = ser.validated_data['methode']
        apparie    = ser.validated_data['apparie']

        try:
            df = get_dataset_data(dataset_id)
        except Exception as e:
            return _err(f"Impossible de récupérer les données : {e}", code=502)

        for col in [colonne, col_groupe]:
            if col not in df.columns:
                return _err(f"Colonne '{col}' introuvable dans le dataset.")

        # Extraire les groupes
        groupes_uniques = df[col_groupe].dropna().unique()
        groupes = [
            df[df[col_groupe] == g][colonne].dropna().tolist()
            for g in groupes_uniques
        ]
        groupes = [g for g in groupes if len(g) >= 2]

        if len(groupes) < 2:
            return _err("Il faut au moins 2 groupes avec des données suffisantes.")

        try:
            if methode == 'ttest' and len(groupes) == 2:
                resultat = test_student(groupes[0], groupes[1], apparie=apparie)
            elif methode == 'mann_whitney' and len(groupes) == 2:
                resultat = test_mann_whitney(groupes[0], groupes[1])
            elif methode == 'anova':
                resultat = test_anova(*groupes)
            elif methode == 'kruskal':
                from scipy import stats as scipy_stats
                gs = [pd.to_numeric(pd.Series(g), errors='coerce').dropna() for g in groupes]
                stat, p = scipy_stats.kruskal(*gs)
                resultat = {
                    'statistique': round(float(stat), 4),
                    'p_value':     round(float(p), 6),
                    'decision':    'Différence significative' if p < 0.05 else 'Pas de différence significative',
                    'methode':     'Kruskal-Wallis',
                    'nb_groupes':  len(groupes),
                    'alpha':       0.05,
                }
            else:
                # Fallback : t-test si 2 groupes, ANOVA sinon
                if len(groupes) == 2:
                    resultat = test_student(groupes[0], groupes[1])
                else:
                    resultat = test_anova(*groupes)
        except Exception as e:
            return _err(f"Erreur lors du test : {e}", code=500)

        return _ok({
            'dataset_id':      dataset_id,
            'colonne':         colonne,
            'col_groupe':      col_groupe,
            'nb_groupes':      len(groupes),
            'groupes':         [str(g) for g in groupes_uniques[:len(groupes)]],
            'effectifs':       [len(g) for g in groupes],
            'resultat':        resultat,
        })


# ══════════════════════════════════════════════════
# 3. INDÉPENDANCE — POST /api/v1/tests/independance/
# ══════════════════════════════════════════════════
class IndependanceView(APIView):
    """
    Teste l'indépendance entre deux variables qualitatives.
    Méthode : Chi2 d'indépendance (tableau de contingence).
    """

    def post(self, request):
        ser = IndependanceRequestSerializer(data=request.data)
        if not ser.is_valid():
            return _err("Paramètres invalides.", details=ser.errors)

        dataset_id = str(ser.validated_data['dataset_id'])
        col_var1   = ser.validated_data['col_var1']
        col_var2   = ser.validated_data['col_var2']

        try:
            df = get_dataset_data(dataset_id)
        except Exception as e:
            return _err(f"Impossible de récupérer les données : {e}", code=502)

        for col in [col_var1, col_var2]:
            if col not in df.columns:
                return _err(f"Colonne '{col}' introuvable dans le dataset.")

        # Construire le tableau de contingence
        df_clean = df[[col_var1, col_var2]].dropna()
        if len(df_clean) < 5:
            return _err("Données insuffisantes pour le test Chi2 (minimum 5 observations).")

        try:
            tableau = pd.crosstab(df_clean[col_var1], df_clean[col_var2])
            resultat = test_chi2(tableau.values)
        except Exception as e:
            return _err(f"Erreur lors du test Chi2 : {e}", code=500)

        return _ok({
            'dataset_id':       dataset_id,
            'col_var1':         col_var1,
            'col_var2':         col_var2,
            'n':                int(len(df_clean)),
            'tableau_shape':    list(tableau.shape),
            'modalites_var1':   tableau.index.astype(str).tolist(),
            'modalites_var2':   tableau.columns.astype(str).tolist(),
            'resultat':         resultat,
        })


# ══════════════════════════════════════════════════
# 4. SÉLECTEUR — POST /api/v1/tests/selectionner/
# ══════════════════════════════════════════════════
class SelecteurView(APIView):
    """
    Auto-sélection : reçoit dataset_id + colonne (+ col_groupe optionnel),
    dérive automatiquement type_variable / nb_groupes / normalité.
    """

    def post(self, request):
        ser = SelecteurRequestSerializer(data=request.data)
        if not ser.is_valid():
            return _err("Paramètres invalides.", details=ser.errors)

        dataset_id = str(ser.validated_data['dataset_id'])
        colonne    = ser.validated_data['colonne']
        col_groupe = ser.validated_data.get('col_groupe', '')

        try:
            df = get_dataset_data(dataset_id)
        except Exception as e:
            return _err(f"Impossible de récupérer les données : {e}", code=502)

        if colonne not in df.columns:
            return _err(f"Colonne '{colonne}' introuvable dans le dataset.")

        serie = df[colonne].dropna()

        # Dériver type_variable
        type_variable = 'quantitative' if pd.api.types.is_numeric_dtype(serie) else 'qualitative'

        # Dériver nb_groupes
        nb_groupes = 2
        if col_groupe and col_groupe in df.columns:
            nb_groupes = int(df[col_groupe].nunique())

        # Dériver normalité (Shapiro si n ≤ 5000, sinon supposer non-normale)
        normal = False
        if type_variable == 'quantitative' and len(serie) >= 3:
            try:
                from scipy import stats as sp
                sample = serie if len(serie) <= 5000 else serie.sample(5000, random_state=42)
                _, p = sp.shapiro(sample)
                normal = bool(p > 0.05)
            except Exception:
                normal = False

        recommandation = selectionner_test(
            type_variable=type_variable,
            nb_groupes=nb_groupes,
            apparie=False,
            normal=normal,
        )

        return _ok({
            'colonne':       colonne,
            'type_variable': type_variable,
            'nb_groupes':    nb_groupes,
            'normal':        normal,
            **recommandation,   # aplatit test_recommande, nom, alternatives, etc.
        })
