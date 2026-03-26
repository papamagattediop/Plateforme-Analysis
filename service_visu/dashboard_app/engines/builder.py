"""
Moteur de génération des graphiques du dashboard builder.
Utilise Plotly pour produire des JSON Chart.js compatibles.
Appelé par views.py — jamais directement depuis les templates.
"""
import pandas as pd
import json


# ── Types de graphiques supportés ────────────────────────────
TYPES_SUPPORTES = ['bar', 'line', 'pie', 'scatter', 'histogram', 'heatmap', 'table']


def generer_config_graphique(
    df: pd.DataFrame,
    type_widget: str,
    variable_x: str,
    variable_y: str = None,
    titre: str = '',
    filtres: dict = None,
) -> dict:
    """
    Génère la configuration Chart.js pour un widget.

    Args:
        df         : DataFrame des données
        type_widget: type de graphique (bar, line, pie, scatter...)
        variable_x : colonne axe X (ou variable principale)
        variable_y : colonne axe Y (optionnel selon le type)
        titre      : titre du graphique
        filtres    : dict de filtres à appliquer {colonne: valeur}

    Returns:
        dict avec 'labels', 'datasets', 'options' pour Chart.js
    """
    # Appliquer les filtres
    if filtres:
        for col, val in filtres.items():
            if col in df.columns and val:
                df = df[df[col].astype(str) == str(val)]

    if df.empty:
        return {'erreur': 'Aucune donnée après filtrage'}

    if type_widget == 'bar':
        return _config_bar(df, variable_x, variable_y, titre)
    elif type_widget == 'line':
        return _config_line(df, variable_x, variable_y, titre)
    elif type_widget == 'pie':
        return _config_pie(df, variable_x, variable_y, titre)
    elif type_widget == 'scatter':
        return _config_scatter(df, variable_x, variable_y, titre)
    elif type_widget == 'histogram':
        return _config_histogram(df, variable_x, titre)
    elif type_widget == 'table':
        return _config_table(df, variable_x, variable_y)
    elif type_widget == 'heatmap':
        return _config_heatmap(df, variable_x, variable_y, titre)
    else:
        return {'erreur': f"Type '{type_widget}' non supporté"}


# ── Graphique en barres ───────────────────────────────────────
def _config_bar(df, variable_x, variable_y, titre):
    df[variable_x] = df[variable_x].astype(str)

    if variable_y and variable_y in df.columns:
        df[variable_y] = pd.to_numeric(df[variable_y], errors='coerce')
        agg = df.groupby(variable_x)[variable_y].mean().reset_index()
        labels = agg[variable_x].tolist()
        valeurs = [round(float(v), 2) for v in agg[variable_y]]
        label_y = variable_y
    else:
        freq = df[variable_x].value_counts()
        labels = freq.index.tolist()
        valeurs = freq.values.tolist()
        label_y = 'Effectif'

    return {
        'type':  'bar',
        'titre': titre,
        'data': {
            'labels': labels,
            'datasets': [{
                'label':           label_y,
                'data':            valeurs,
                'backgroundColor': _palette_couleurs(len(labels)),
                'borderRadius':    4,
            }],
        },
        'options': {
            'responsive':          True,
            'maintainAspectRatio': False,
            'plugins': {'legend': {'display': False},
                        'title': {'display': bool(titre), 'text': titre}},
            'scales': {'y': {'beginAtZero': True}},
        },
    }


# ── Graphique en lignes ───────────────────────────────────────
def _config_line(df, variable_x, variable_y, titre):
    if not variable_y or variable_y not in df.columns:
        return {'erreur': 'variable_y requis pour un graphique en lignes'}

    df[variable_y] = pd.to_numeric(df[variable_y], errors='coerce')
    df = df.dropna(subset=[variable_y]).sort_values(variable_x)

    labels  = df[variable_x].astype(str).tolist()
    valeurs = [round(float(v), 2) for v in df[variable_y]]

    return {
        'type':  'line',
        'titre': titre,
        'data': {
            'labels': labels,
            'datasets': [{
                'label':       variable_y,
                'data':        valeurs,
                'borderColor':      '#2563EB',
                'backgroundColor':  'rgba(37,99,235,0.1)',
                'borderWidth':      2,
                'pointRadius':      3,
                'tension':          0.3,
                'fill':             True,
            }],
        },
        'options': {
            'responsive':          True,
            'maintainAspectRatio': False,
            'plugins': {'title': {'display': bool(titre), 'text': titre}},
            'scales':  {'y': {'beginAtZero': False}},
        },
    }


# ── Camembert ─────────────────────────────────────────────────
def _config_pie(df, variable_x, variable_y, titre):
    if variable_y and variable_y in df.columns:
        df[variable_y] = pd.to_numeric(df[variable_y], errors='coerce')
        agg = df.groupby(variable_x, as_index=False)[variable_y].sum()
        labels  = agg[variable_x].astype(str).tolist()
        valeurs = [round(float(v), 2) for v in agg[variable_y]]
    else:
        freq    = df[variable_x].value_counts().head(10)
        labels  = freq.index.astype(str).tolist()
        valeurs = freq.values.tolist()

    return {
        'type':  'pie',
        'titre': titre,
        'data': {
            'labels': labels,
            'datasets': [{
                'data':            valeurs,
                'backgroundColor': _palette_couleurs(len(labels)),
                'borderWidth':     2,
                'borderColor':     '#ffffff',
            }],
        },
        'options': {
            'responsive':          True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'position': 'right'},
                'title':  {'display': bool(titre), 'text': titre},
            },
        },
    }


# ── Nuage de points ───────────────────────────────────────────
def _config_scatter(df, variable_x, variable_y, titre):
    if not variable_y or variable_y not in df.columns:
        return {'erreur': 'variable_y requis pour un nuage de points'}

    df[variable_x] = pd.to_numeric(df[variable_x], errors='coerce')
    df[variable_y] = pd.to_numeric(df[variable_y], errors='coerce')
    df = df.dropna(subset=[variable_x, variable_y])

    # Limiter à 500 points pour les performances
    if len(df) > 500:
        df = df.sample(500, random_state=42)

    points = [
        {'x': round(float(r[variable_x]), 4),
         'y': round(float(r[variable_y]), 4)}
        for _, r in df.iterrows()
    ]

    return {
        'type':  'scatter',
        'titre': titre,
        'data': {
            'datasets': [{
                'label':           f'{variable_x} vs {variable_y}',
                'data':            points,
                'backgroundColor': 'rgba(37,99,235,0.5)',
                'pointRadius':     4,
            }],
        },
        'options': {
            'responsive':          True,
            'maintainAspectRatio': False,
            'plugins': {'title': {'display': bool(titre), 'text': titre}},
            'scales': {
                'x': {'title': {'display': True, 'text': variable_x}},
                'y': {'title': {'display': True, 'text': variable_y}},
            },
        },
    }


# ── Histogramme ───────────────────────────────────────────────
def _config_histogram(df, variable_x, titre):
    df[variable_x] = pd.to_numeric(df[variable_x], errors='coerce')
    serie = df[variable_x].dropna()

    if serie.empty:
        return {'erreur': f"'{variable_x}' ne contient pas de valeurs numériques"}

    # Créer les bins
    nb_bins = min(20, int(len(serie) ** 0.5) + 5)
    counts, edges = pd.cut(serie, bins=nb_bins, retbins=True)
    freq = counts.value_counts().sort_index()

    labels  = [f'{round(i.left, 1)}–{round(i.right, 1)}' for i in freq.index]
    valeurs = freq.values.tolist()

    return {
        'type':  'bar',
        'titre': titre or f'Distribution de {variable_x}',
        'data': {
            'labels': labels,
            'datasets': [{
                'label':           'Fréquence',
                'data':            valeurs,
                'backgroundColor': 'rgba(37,99,235,0.7)',
                'borderColor':     '#2563EB',
                'borderWidth':     1,
                'borderRadius':    0,
            }],
        },
        'options': {
            'responsive':          True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'display': False},
                'title':  {'display': bool(titre), 'text': titre},
            },
            'scales': {
                'x': {'title': {'display': True, 'text': variable_x}},
                'y': {'beginAtZero': True,
                      'title': {'display': True, 'text': 'Fréquence'}},
            },
        },
    }


# ── Heatmap de corrélation ────────────────────────────────────
def _config_heatmap(df, variable_x, variable_y, titre):
    """
    Heatmap de corrélation entre deux variables numériques ou
    matrice de corrélation si variable_y vaut 'all'.
    Retourne un format compatible avec Chart.js via plugin matrix.
    """
    # Cas 1 : matrice de corrélation sur toutes les colonnes numériques
    if not variable_y or variable_y == 'all':
        numeriques = df.select_dtypes(include='number').columns.tolist()
        if len(numeriques) < 2:
            return {'erreur': 'Pas assez de colonnes numériques pour une heatmap'}
        numeriques = numeriques[:10]  # Limiter à 10 variables
        matrice = df[numeriques].corr().round(3)
        labels  = numeriques
        valeurs = []
        for i, col_i in enumerate(labels):
            for j, col_j in enumerate(labels):
                valeurs.append({
                    'x': j,
                    'y': i,
                    'v': round(float(matrice.loc[col_i, col_j]), 3),
                })
        return {
            'type':   'heatmap',
            'titre':  titre or 'Matrice de corrélation',
            'labels': labels,
            'data': {
                'datasets': [{
                    'label': 'Corrélation',
                    'data':  valeurs,
                }],
            },
            'options': {
                'responsive':          True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title':  {'display': bool(titre), 'text': titre},
                    'legend': {'display': False},
                },
                'scales': {
                    'x': {'labels': labels},
                    'y': {'labels': labels, 'reverse': True},
                },
            },
        }

    # Cas 2 : croisement variable_x (quanti) × variable_y (quali) — moyennes par groupe
    if variable_x not in df.columns or variable_y not in df.columns:
        return {'erreur': f"Colonnes '{variable_x}' ou '{variable_y}' introuvables"}

    df[variable_x] = pd.to_numeric(df[variable_x], errors='coerce')
    pivot = df.groupby(variable_y)[variable_x].mean().reset_index()
    pivot = pivot.dropna().head(20)

    labels_x  = pivot[variable_y].astype(str).tolist()
    valeurs_y = [round(float(v), 3) for v in pivot[variable_x]]
    data_pts   = [{'x': i, 'y': 0, 'v': v} for i, v in enumerate(valeurs_y)]

    return {
        'type':   'heatmap',
        'titre':  titre or f'{variable_x} par {variable_y}',
        'labels': labels_x,
        'data': {
            'datasets': [{
                'label': variable_x,
                'data':  data_pts,
            }],
        },
        'options': {
            'responsive':          True,
            'maintainAspectRatio': False,
            'plugins': {
                'title':  {'display': bool(titre), 'text': titre},
                'legend': {'display': False},
            },
        },
    }


# ── Tableau ───────────────────────────────────────────────────
def _config_table(df, variable_x, variable_y):
    colonnes = [variable_x]
    if variable_y and variable_y in df.columns:
        colonnes.append(variable_y)

    df_table = df[colonnes].head(50)

    return {
        'type':     'table',
        'colonnes': colonnes,
        'lignes':   df_table.fillna('').astype(str).values.tolist(),
        'nb_total': len(df),
    }


# ── Palette de couleurs ───────────────────────────────────────
def _palette_couleurs(n: int) -> list:
    """Retourne n couleurs pour les graphiques."""
    couleurs = [
        'rgba(37,99,235,0.8)',   # bleu
        'rgba(16,185,129,0.8)',  # vert
        'rgba(245,158,11,0.8)',  # orange
        'rgba(239,68,68,0.8)',   # rouge
        'rgba(139,92,246,0.8)',  # violet
        'rgba(20,184,166,0.8)',  # teal
        'rgba(249,115,22,0.8)',  # orange foncé
        'rgba(236,72,153,0.8)',  # rose
        'rgba(100,116,139,0.8)', # gris bleu
        'rgba(6,182,212,0.8)',   # cyan
    ]
    # Répéter si plus de couleurs nécessaires
    return [couleurs[i % len(couleurs)] for i in range(n)]