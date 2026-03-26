# stats_app/utils/stats.py
"""
Moteur de calculs statistiques complet.
Couvre : univarié quantitatif, univarié catégoriel,
numérique × numérique, catégoriel × catégoriel,
catégoriel × numérique, régressions.
"""
import pandas as pd
import numpy as np
from scipy import stats as sp_stats


# ══════════════════════════════════════════════════════════
# 1. VARIABLE QUANTITATIVE SEULE (univarié)
# ══════════════════════════════════════════════════════════

def stats_descriptives(df, column):
    """Toutes les stats descriptives pour une variable numérique."""
    series = pd.to_numeric(df[column], errors='coerce').dropna()
    return {
        'column': column,
        'count': int(series.count()),
        'mean': round(float(series.mean()), 4),
        'median': round(float(series.median()), 4),
        'mode': round(float(series.mode().iloc[0]), 4) if not series.mode().empty else None,
        'geometric_mean': round(float(sp_stats.gmean(series[series > 0])), 4) if (series > 0).all() else None,
        'std': round(float(series.std()), 4),
        'variance': round(float(series.var()), 4),
        'min': round(float(series.min()), 4),
        'max': round(float(series.max()), 4),
        'range': round(float(series.max() - series.min()), 4),
        'q1': round(float(series.quantile(0.25)), 4),
        'q3': round(float(series.quantile(0.75)), 4),
        'iqr': round(float(series.quantile(0.75) - series.quantile(0.25)), 4),
        'skewness': round(float(series.skew()), 4),
        'kurtosis': round(float(series.kurtosis()), 4),
        'sem': round(float(series.sem()), 4),  # erreur standard de la moyenne
        'cv': round(float(series.std() / series.mean() * 100), 2) if series.mean() != 0 else None,  # coeff de variation
        'missing': int(df[column].isna().sum()),
    }


def confidence_interval(df, column, confidence=0.95):
    """Intervalle de confiance pour la moyenne (distribution de Student)."""
    series = pd.to_numeric(df[column], errors='coerce').dropna()
    n = len(series)
    mean = float(series.mean())
    sem = float(series.sem())
    dof = n - 1
    t_crit = float(sp_stats.t.ppf((1 + confidence) / 2, dof))
    margin = t_crit * sem
    return {
        'column': column,
        'mean': round(mean, 4),
        'confidence_level': confidence,
        'margin_of_error': round(margin, 4),
        'ci_lower': round(mean - margin, 4),
        'ci_upper': round(mean + margin, 4),
        'n': n,
        'degrees_of_freedom': dof,
    }


def distribution_fit(df, column):
    """Teste l'ajustement à une loi normale (Shapiro + Kolmogorov-Smirnov)."""
    series = pd.to_numeric(df[column], errors='coerce').dropna()
    sample = series.sample(min(len(series), 5000), random_state=42)

    # Shapiro-Wilk
    shap_stat, shap_p = sp_stats.shapiro(sample)

    # Kolmogorov-Smirnov (compare à une normale de même moyenne/écart-type)
    ks_stat, ks_p = sp_stats.kstest(series, 'norm', args=(series.mean(), series.std()))

    return {
        'column': column,
        'shapiro': {
            'statistic': round(float(shap_stat), 6),
            'p_value': round(float(shap_p), 6),
            'normal': shap_p > 0.05,
        },
        'kolmogorov_smirnov': {
            'statistic': round(float(ks_stat), 6),
            'p_value': round(float(ks_p), 6),
            'normal': ks_p > 0.05,
        },
        'interpretation': 'Distribution normale' if (shap_p > 0.05 and ks_p > 0.05)
                          else 'Distribution non normale',
    }


def histogram_data(df, column, bins=20):
    """Données pour construire un histogramme + KDE côté frontend."""
    series = pd.to_numeric(df[column], errors='coerce').dropna()
    counts, bin_edges = np.histogram(series, bins=bins)
    return {
        'column': column,
        'counts': counts.tolist(),
        'bin_edges': [round(float(b), 4) for b in bin_edges],
        'kde_x': np.linspace(float(series.min()), float(series.max()), 100).tolist(),
        'kde_y': sp_stats.gaussian_kde(series)(
            np.linspace(float(series.min()), float(series.max()), 100)
        ).tolist(),
    }


def boxplot_data(df, column):
    """Données pour construire un boxplot côté frontend."""
    series = pd.to_numeric(df[column], errors='coerce').dropna()
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    whisker_low = float(series[series >= q1 - 1.5 * iqr].min())
    whisker_high = float(series[series <= q3 + 1.5 * iqr].max())
    outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
    return {
        'column': column,
        'min': whisker_low,
        'q1': round(q1, 4),
        'median': round(float(series.median()), 4),
        'q3': round(q3, 4),
        'max': whisker_high,
        'outliers': [round(float(o), 4) for o in outliers],
        'n_outliers': len(outliers),
    }


# ══════════════════════════════════════════════════════════
# 2. VARIABLE CATÉGORIELLE SEULE (univarié)
# ══════════════════════════════════════════════════════════

def freq_table(df, column):
    """Tableau de fréquences pour variable catégorielle."""
    counts = df[column].value_counts()
    total = int(counts.sum())
    freq_rel = (counts / total * 100).round(2)
    freq_cum = freq_rel.cumsum().round(2)
    return {
        'column': column,
        'total': total,
        'categories': [
            {
                'value': str(val),
                'count': int(counts[val]),
                'frequency_pct': float(freq_rel[val]),
                'cumulative_pct': float(freq_cum[val]),
            }
            for val in counts.index
        ],
        'n_categories': int(counts.nunique()),
        'mode': str(counts.index[0]),
        'mode_count': int(counts.iloc[0]),
    }


# ══════════════════════════════════════════════════════════
# 3. NUMÉRIQUE × NUMÉRIQUE (bivariée)
# ══════════════════════════════════════════════════════════

def correlation_deux_variables(df, col_x, col_y):
    """Analyse complète entre 2 variables numériques : Pearson, Spearman, Kendall."""
    x = pd.to_numeric(df[col_x], errors='coerce')
    y = pd.to_numeric(df[col_y], errors='coerce')
    combined = pd.DataFrame({'x': x, 'y': y}).dropna()
    xc, yc = combined['x'], combined['y']

    # Pearson (linéaire)
    pearson_r, pearson_p = sp_stats.pearsonr(xc, yc)

    # Spearman (monotone, rangs)
    spearman_r, spearman_p = sp_stats.spearmanr(xc, yc)

    # Kendall (concordance)
    kendall_tau, kendall_p = sp_stats.kendalltau(xc, yc)

    return {
        'col_x': col_x,
        'col_y': col_y,
        'n': len(combined),
        'pearson': {
            'r': round(float(pearson_r), 4),
            'p_value': round(float(pearson_p), 6),
            'significant': pearson_p < 0.05,
        },
        'spearman': {
            'rho': round(float(spearman_r), 4),
            'p_value': round(float(spearman_p), 6),
            'significant': spearman_p < 0.05,
        },
        'kendall': {
            'tau': round(float(kendall_tau), 4),
            'p_value': round(float(kendall_p), 6),
            'significant': kendall_p < 0.05,
        },
        'covariance': round(float(np.cov(xc, yc)[0, 1]), 4),
        'r_squared': round(float(pearson_r ** 2), 4),
    }


def regression_lineaire(df, col_x, col_y):
    """Régression linéaire simple avec statsmodels."""
    import statsmodels.api as sm

    x = pd.to_numeric(df[col_x], errors='coerce')
    y = pd.to_numeric(df[col_y], errors='coerce')
    combined = pd.DataFrame({'x': x, 'y': y}).dropna()

    X = sm.add_constant(combined['x'])
    model = sm.OLS(combined['y'], X).fit()

    return {
        'col_x': col_x,
        'col_y': col_y,
        'intercept': round(float(model.params.iloc[0]), 4),
        'slope': round(float(model.params.iloc[1]), 4),
        'r_squared': round(float(model.rsquared), 4),
        'adj_r_squared': round(float(model.rsquared_adj), 4),
        'f_statistic': round(float(model.fvalue), 4),
        'f_p_value': round(float(model.f_pvalue), 6),
        'aic': round(float(model.aic), 2),
        'bic': round(float(model.bic), 2),
        'coefficients': [
            {
                'name': name,
                'value': round(float(model.params[name]), 4),
                'std_error': round(float(model.bse[name]), 4),
                't_value': round(float(model.tvalues[name]), 4),
                'p_value': round(float(model.pvalues[name]), 6),
                'ci_lower': round(float(model.conf_int().loc[name][0]), 4),
                'ci_upper': round(float(model.conf_int().loc[name][1]), 4),
            }
            for name in model.params.index
        ],
        'durbin_watson': round(float(sm.stats.durbin_watson(model.resid)), 4),
        'n': int(model.nobs),
    }


def regression_polynomiale(df, col_x, col_y, degree=2):
    """Régression polynomiale (degré 2, 3...)."""
    import statsmodels.api as sm

    x = pd.to_numeric(df[col_x], errors='coerce')
    y = pd.to_numeric(df[col_y], errors='coerce')
    combined = pd.DataFrame({'x': x, 'y': y}).dropna()

    # Construire la matrice de plan
    X = np.column_stack([combined['x'] ** i for i in range(1, degree + 1)])
    X = sm.add_constant(X)
    model = sm.OLS(combined['y'], X).fit()

    return {
        'col_x': col_x,
        'col_y': col_y,
        'degree': degree,
        'r_squared': round(float(model.rsquared), 4),
        'adj_r_squared': round(float(model.rsquared_adj), 4),
        'aic': round(float(model.aic), 2),
        'bic': round(float(model.bic), 2),
        'coefficients': [round(float(c), 6) for c in model.params],
        'n': int(model.nobs),
    }


def correlation_matrix(df, columns):
    """Matrice de corrélation (Pearson) entre plusieurs variables numériques."""
    numeric_df = df[columns].apply(pd.to_numeric, errors='coerce').dropna()
    corr = numeric_df.corr().round(4)
    return {
        'columns': corr.columns.tolist(),
        'matrix': corr.values.tolist(),
    }


def scatter_data(df, col_x, col_y):
    """Données pour nuage de points (frontend)."""
    x = pd.to_numeric(df[col_x], errors='coerce')
    y = pd.to_numeric(df[col_y], errors='coerce')
    combined = pd.DataFrame({'x': x, 'y': y}).dropna()
    # Limiter à 1000 points pour le frontend
    if len(combined) > 1000:
        combined = combined.sample(1000, random_state=42)
    return {
        'col_x': col_x,
        'col_y': col_y,
        'points': combined.values.tolist(),
        'n': len(combined),
    }


# ══════════════════════════════════════════════════════════
# 4. CATÉGORIEL × CATÉGORIEL
# ══════════════════════════════════════════════════════════

def contingency_table(df, col1, col2):
    """Tableau de contingence complet avec fréquences et Chi2."""
    ct = pd.crosstab(df[col1], df[col2])
    ct_pct = pd.crosstab(df[col1], df[col2], normalize='all').round(4) * 100

    # Chi2
    chi2, p, dof, expected = sp_stats.chi2_contingency(ct)

    # V de Cramer (force de l'association)
    n = ct.sum().sum()
    min_dim = min(ct.shape[0], ct.shape[1]) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

    return {
        'col1': col1,
        'col2': col2,
        'contingency': ct.to_dict(),
        'contingency_pct': ct_pct.to_dict(),
        'expected': pd.DataFrame(
            expected, index=ct.index, columns=ct.columns
        ).round(2).to_dict(),
        'chi2': {
            'statistic': round(float(chi2), 4),
            'p_value': round(float(p), 6),
            'dof': int(dof),
            'significant': p < 0.05,
        },
        'cramers_v': round(float(cramers_v), 4),
        'interpretation': _interpret_cramers_v(cramers_v),
        'n': int(n),
    }


def _interpret_cramers_v(v):
    if v < 0.1:
        return 'Association negligeable'
    elif v < 0.3:
        return 'Association faible'
    elif v < 0.5:
        return 'Association moderee'
    else:
        return 'Association forte'


# ══════════════════════════════════════════════════════════
# 5. CATÉGORIEL × NUMÉRIQUE
# ══════════════════════════════════════════════════════════

def stats_par_groupe(df, col_numeric, col_group):
    """Stats descriptives d'une variable numérique ventilées par groupe."""
    result = []
    grouped = df.groupby(col_group)[col_numeric]

    for name, group in grouped:
        series = pd.to_numeric(group, errors='coerce').dropna()
        if len(series) == 0:
            continue
        result.append({
            'group': str(name),
            'count': int(len(series)),
            'mean': round(float(series.mean()), 4),
            'median': round(float(series.median()), 4),
            'std': round(float(series.std()), 4),
            'min': round(float(series.min()), 4),
            'max': round(float(series.max()), 4),
            'q1': round(float(series.quantile(0.25)), 4),
            'q3': round(float(series.quantile(0.75)), 4),
        })

    return {
        'col_numeric': col_numeric,
        'col_group': col_group,
        'groups': result,
        'n_groups': len(result),
    }


def test_anova(df, col_numeric, col_group):
    """ANOVA à un facteur : compare les moyennes entre groupes."""
    groups = [
        pd.to_numeric(group[col_numeric], errors='coerce').dropna().values
        for _, group in df.groupby(col_group)
        if len(group[col_numeric].dropna()) >= 2
    ]
    if len(groups) < 2:
        return {'error': 'Au moins 2 groupes avec 2+ observations'}

    f_stat, p = sp_stats.f_oneway(*groups)
    
    # Eta-carré (taille d'effet)
    all_data = np.concatenate(groups)
    grand_mean = np.mean(all_data)
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    ss_total = np.sum((all_data - grand_mean) ** 2)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    return {
        'test': 'ANOVA one-way',
        'f_statistic': round(float(f_stat), 4),
        'p_value': round(float(p), 6),
        'nb_groups': len(groups),
        'significant': p < 0.05,
        'eta_squared': round(float(eta_squared), 4),
        'interpretation': _interpret_eta(eta_squared),
    }


def _interpret_eta(eta):
    if eta < 0.01:
        return 'Effet negligeable'
    elif eta < 0.06:
        return 'Petit effet'
    elif eta < 0.14:
        return 'Effet moyen'
    else:
        return 'Grand effet'


def test_ttest(df, col_numeric, col_group):
    """t-test de Student entre 2 groupes."""
    groups = df.groupby(col_group)[col_numeric]
    group_names = list(groups.groups.keys())

    if len(group_names) < 2:
        return {'error': 'Il faut exactement 2 groupes'}

    data1 = pd.to_numeric(groups.get_group(group_names[0]), errors='coerce').dropna()
    data2 = pd.to_numeric(groups.get_group(group_names[1]), errors='coerce').dropna()

    # Test de Levene pour égalité des variances
    lev_stat, lev_p = sp_stats.levene(data1, data2)
    equal_var = lev_p > 0.05

    # t-test (Welch si variances inégales)
    stat, p = sp_stats.ttest_ind(data1, data2, equal_var=equal_var)

    return {
        'test': 't-Student' if equal_var else 't-Welch',
        'group1': str(group_names[0]),
        'group2': str(group_names[1]),
        'mean1': round(float(data1.mean()), 4),
        'mean2': round(float(data2.mean()), 4),
        'statistic': round(float(stat), 4),
        'p_value': round(float(p), 6),
        'significant': p < 0.05,
        'levene': {
            'statistic': round(float(lev_stat), 4),
            'p_value': round(float(lev_p), 6),
            'equal_variance': equal_var,
        },
    }


def test_mann_whitney(df, col_numeric, col_group):
    """Mann-Whitney U (alternative non paramétrique au t-test)."""
    groups = df.groupby(col_group)[col_numeric]
    group_names = list(groups.groups.keys())[:2]

    data1 = pd.to_numeric(groups.get_group(group_names[0]), errors='coerce').dropna()
    data2 = pd.to_numeric(groups.get_group(group_names[1]), errors='coerce').dropna()

    stat, p = sp_stats.mannwhitneyu(data1, data2, alternative='two-sided')

    return {
        'test': 'Mann-Whitney U',
        'group1': str(group_names[0]),
        'group2': str(group_names[1]),
        'statistic': round(float(stat), 4),
        'p_value': round(float(p), 6),
        'significant': p < 0.05,
    }


def test_kruskal(df, col_numeric, col_group):
    """Kruskal-Wallis (alternative non paramétrique à l'ANOVA)."""
    groups = [
        pd.to_numeric(group[col_numeric], errors='coerce').dropna().values
        for _, group in df.groupby(col_group)
        if len(group[col_numeric].dropna()) >= 2
    ]
    if len(groups) < 2:
        return {'error': 'Au moins 2 groupes necessaires'}

    stat, p = sp_stats.kruskal(*groups)
    return {
        'test': 'Kruskal-Wallis',
        'statistic': round(float(stat), 4),
        'p_value': round(float(p), 6),
        'nb_groups': len(groups),
        'significant': p < 0.05,
    }


def test_fisher_variance(df, col_numeric, col_group):
    """Test F de Fisher pour comparer 2 variances."""
    groups = df.groupby(col_group)[col_numeric]
    group_names = list(groups.groups.keys())[:2]

    data1 = pd.to_numeric(groups.get_group(group_names[0]), errors='coerce').dropna()
    data2 = pd.to_numeric(groups.get_group(group_names[1]), errors='coerce').dropna()

    var1 = float(data1.var(ddof=1))
    var2 = float(data2.var(ddof=1))
    f_val = var1 / var2 if var2 > 0 else float('inf')
    dfn = len(data1) - 1
    dfd = len(data2) - 1

    p = float(sp_stats.f.cdf(f_val, dfn, dfd))
    p_two_tail = 2 * min(p, 1 - p)

    return {
        'test': 'Fisher F (egalite des variances)',
        'f_statistic': round(f_val, 4),
        'var1': round(var1, 4),
        'var2': round(var2, 4),
        'df1': dfn,
        'df2': dfd,
        'p_value': round(p_two_tail, 6),
        'significant': p_two_tail < 0.05,
    }


def boxplot_par_groupe(df, col_numeric, col_group):
    """Données de boxplot ventilées par groupe (frontend)."""
    result = []
    for name, group in df.groupby(col_group):
        series = pd.to_numeric(group[col_numeric], errors='coerce').dropna()
        if len(series) == 0:
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        result.append({
            'group': str(name),
            'min': round(float(series[series >= q1 - 1.5 * iqr].min()), 4),
            'q1': round(q1, 4),
            'median': round(float(series.median()), 4),
            'q3': round(q3, 4),
            'max': round(float(series[series <= q3 + 1.5 * iqr].max()), 4),
            'mean': round(float(series.mean()), 4),
        })
    return {'col_numeric': col_numeric, 'col_group': col_group, 'groups': result}

