'''
Moteur de calcul statistiques descriptives.
Appele par stats_app/views.py.
'''
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def calc_univarie_quantitatif(serie: pd.Series) -> dict:
    '''Statistiques descriptives d'une variable quantitative.'''
    s = pd.to_numeric(serie.dropna(), errors='coerce').dropna()
    return {
        'n':          int(len(s)),
        'moyenne':    round(float(s.mean()), 4),
        'mediane':    round(float(s.median()), 4),
        'mode':       round(float(s.mode()[0]), 4) if len(s.mode()) else None,
        'variance':   round(float(s.var()), 4),
        'ecart_type': round(float(s.std()), 4),
        'min':        round(float(s.min()), 4),
        'max':        round(float(s.max()), 4),
        'q1':         round(float(s.quantile(0.25)), 4),
        'q3':         round(float(s.quantile(0.75)), 4),
        'iqr':        round(float(s.quantile(0.75) - s.quantile(0.25)), 4),
        'asymetrie':  round(float(scipy_stats.skew(s)), 4),
        'kurtosis':   round(float(scipy_stats.kurtosis(s)), 4),
    }


def calc_univarie_qualitatif(serie: pd.Series) -> dict:
    '''Frequences d'une variable qualitative.'''
    freq = serie.value_counts()
    freq_rel = serie.value_counts(normalize=True)
    return {
        'n':        int(len(serie.dropna())),
        'n_uniques': int(serie.nunique()),
        'modalites': [
            {'valeur': str(k), 'effectif': int(v), 'frequence': round(float(freq_rel[k]), 4)}
            for k, v in freq.items()
        ],
    }


def calc_bivarie(df: pd.DataFrame, col1: str, col2: str) -> dict:
    '''Analyse bivariee entre deux variables.'''
    s1 = pd.to_numeric(df[col1], errors='coerce').dropna()
    s2 = pd.to_numeric(df[col2], errors='coerce').dropna()
    idx = s1.index.intersection(s2.index)
    s1, s2 = s1[idx], s2[idx]
    r_pearson, p_pearson = scipy_stats.pearsonr(s1, s2)
    r_spearman, p_spearman = scipy_stats.spearmanr(s1, s2)
    return {
        'n':              int(len(s1)),
        'pearson_r':      round(float(r_pearson), 4),
        'pearson_p':      round(float(p_pearson), 6),
        'spearman_r':     round(float(r_spearman), 4),
        'spearman_p':     round(float(p_spearman), 6),
        'scatter_points': list(zip(s1.tolist()[:200], s2.tolist()[:200])),
    }
