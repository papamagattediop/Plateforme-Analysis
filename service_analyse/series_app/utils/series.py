import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, kpss


def test_adf(series):
    clean = pd.to_numeric(pd.Series(series), errors='coerce').dropna()
    result = adfuller(clean, autolag='AIC')
    return {
        'test': 'ADF',
        'statistic': round(float(result[0]), 4),
        'p_value': round(float(result[1]), 6),
        'stationary': result[1] < 0.05,
    }


def test_kpss_stationarity(series):
    clean = pd.to_numeric(pd.Series(series), errors='coerce').dropna()
    stat, p, _, _ = kpss(clean, regression='c', nlags='auto')
    return {
        'test': 'KPSS',
        'statistic': round(float(stat), 4),
        'p_value': round(float(p), 6),
        'stationary': p > 0.05,
    }


def fit_arima(series, order=(1, 1, 1), periods=5):
    clean = pd.to_numeric(pd.Series(series), errors='coerce').dropna()
    model = ARIMA(clean, order=order)
    fitted = model.fit()
    forecast = fitted.get_forecast(steps=periods)
    pred = forecast.predicted_mean
    conf = forecast.conf_int(alpha=0.05)

    return {
        'order': list(order),
        'aic': round(float(fitted.aic), 2),
        'bic': round(float(fitted.bic), 2),
        'forecast': [round(float(v), 4) for v in pred],
        'conf_lower': [round(float(v), 4) for v in conf.iloc[:, 0]],
        'conf_upper': [round(float(v), 4) for v in conf.iloc[:, 1]],
    }


def fit_prophet(df_ts, periods=5, freq='YS'):
    from prophet import Prophet
    model = Prophet(yearly_seasonality=True)
    model.fit(df_ts)
    future = model.make_future_dataframe(periods=periods, freq=freq)
    forecast = model.predict(future)
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
    result['ds'] = result['ds'].astype(str)
    return {'forecast': result.to_dict(orient='records')}