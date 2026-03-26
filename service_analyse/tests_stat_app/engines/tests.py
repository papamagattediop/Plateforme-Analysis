'''
Moteur de tests statistiques — SciPy, Statsmodels, Pingouin.
'''
from scipy import stats as scipy_stats
import pandas as pd


def test_normalite(serie: pd.Series, methode: str = 'shapiro') -> dict:
    s = pd.to_numeric(serie.dropna(), errors='coerce').dropna()
    if methode == 'shapiro':
        stat, p = scipy_stats.shapiro(s)
    elif methode == 'kstest':
        stat, p = scipy_stats.kstest(s, 'norm')
    elif methode == 'anderson':
        res = scipy_stats.anderson(s)
        return {'statistique': round(float(res.statistic), 4),
                'valeurs_critiques': res.critical_values.tolist(),
                'niveaux': res.significance_level.tolist(),
                'methode': 'anderson'}
    else:
        raise ValueError(f'Methode inconnue : {methode}')
    return {
        'statistique': round(float(stat), 4),
        'p_value':     round(float(p), 6),
        'decision':    'Normal' if p > 0.05 else 'Non normal',
        'methode':     methode,
        'alpha':       0.05,
    }


def test_student(groupe1, groupe2, apparie=False) -> dict:
    g1 = pd.to_numeric(pd.Series(groupe1).dropna(), errors='coerce').dropna()
    g2 = pd.to_numeric(pd.Series(groupe2).dropna(), errors='coerce').dropna()
    if apparie:
        stat, p = scipy_stats.ttest_rel(g1, g2)
        methode = 't-test apparie'
    else:
        stat, p = scipy_stats.ttest_ind(g1, g2)
        methode = 't-test independant'
    return {
        'statistique': round(float(stat), 4),
        'p_value':     round(float(p), 6),
        'decision':    'Difference significative' if p < 0.05 else 'Pas de difference significative',
        'methode':     methode,
        'alpha':       0.05,
    }


def test_anova(*groupes) -> dict:
    g = [pd.to_numeric(pd.Series(g).dropna(), errors='coerce').dropna() for g in groupes]
    stat, p = scipy_stats.f_oneway(*g)
    return {
        'statistique': round(float(stat), 4),
        'p_value':     round(float(p), 6),
        'decision':    'Difference significative' if p < 0.05 else 'Pas de difference significative',
        'methode':     'ANOVA 1 facteur',
        'nb_groupes':  len(groupes),
        'alpha':       0.05,
    }


def test_chi2(tableau_contingence) -> dict:
    stat, p, ddl, freq_attendues = scipy_stats.chi2_contingency(tableau_contingence)
    return {
        'statistique': round(float(stat), 4),
        'p_value':     round(float(p), 6),
        'ddl':         int(ddl),
        'decision':    'Dependance significative' if p < 0.05 else 'Independance',
        'methode':     'Chi2 independance',
        'alpha':       0.05,
    }


def test_mann_whitney(groupe1, groupe2) -> dict:
    g1 = pd.to_numeric(pd.Series(groupe1).dropna(), errors='coerce').dropna()
    g2 = pd.to_numeric(pd.Series(groupe2).dropna(), errors='coerce').dropna()
    stat, p = scipy_stats.mannwhitneyu(g1, g2, alternative='two-sided')
    return {
        'statistique': round(float(stat), 4),
        'p_value':     round(float(p), 6),
        'decision':    'Difference significative' if p < 0.05 else 'Pas de difference significative',
        'methode':     'Mann-Whitney U',
        'alpha':       0.05,
    }
