'''
Moteur series temporelles — Statsmodels, Prophet, pmdarima.
'''
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.graphics.tsaplots import acf, pacf


def decomposer(serie: pd.Series, periode: int = None) -> dict:
    '''Decomposition tendance / saisonnalite / residus.'''
    if periode is None:
        periode = max(2, len(serie) // 10)
    result = seasonal_decompose(serie.dropna(), model='additive', period=periode)
    return {
        'tendance':     result.trend.dropna().tolist(),
        'saisonnalite': result.seasonal.dropna().tolist(),
        'residus':      result.resid.dropna().tolist(),
        'original':     serie.dropna().tolist(),
    }


def tester_stationnarite(serie: pd.Series) -> dict:
    '''Tests ADF et KPSS de stationnarite.'''
    s = serie.dropna()
    adf_stat, adf_p, _, _, adf_critiques, _ = adfuller(s)
    kpss_stat, kpss_p, _, kpss_critiques = kpss(s, regression='c')
    return {
        'adf': {
            'statistique': round(float(adf_stat), 4),
            'p_value':     round(float(adf_p), 6),
            'decision':    'Stationnaire' if adf_p < 0.05 else 'Non stationnaire',
            'critiques':   {k: round(float(v), 4) for k, v in adf_critiques.items()},
        },
        'kpss': {
            'statistique': round(float(kpss_stat), 4),
            'p_value':     round(float(kpss_p), 6),
            'decision':    'Non stationnaire' if kpss_p < 0.05 else 'Stationnaire',
            'critiques':   {k: round(float(v), 4) for k, v in kpss_critiques.items()},
        },
    }


def calculer_acf_pacf(serie: pd.Series, nlags: int = 20) -> dict:
    '''Calcule les fonctions d autocorrelation ACF et PACF.'''
    s = serie.dropna()
    return {
        'acf':  [round(float(v), 4) for v in acf(s, nlags=nlags)],
        'pacf': [round(float(v), 4) for v in pacf(s, nlags=nlags)],
        'lags': list(range(nlags + 1)),
    }


def prevoir_arima(serie: pd.Series, horizon: int = 12) -> dict:
    '''Prevision avec ARIMA automatique (pmdarima).'''
    import pmdarima as pm
    s = serie.dropna()
    model = pm.auto_arima(s, seasonal=False, stepwise=True, suppress_warnings=True)
    forecast, conf_int = model.predict(n_periods=horizon, return_conf_int=True)
    return {
        'previsions':    [round(float(v), 4) for v in forecast],
        'ic_bas':        [round(float(v), 4) for v in conf_int[:, 0]],
        'ic_haut':       [round(float(v), 4) for v in conf_int[:, 1]],
        'ordre_arima':   str(model.order),
        'aic':           round(float(model.aic()), 2),
    }
