"""Selección técnica SOLO en entrenamiento. No interpreta ADF del spread como prueba independiente."""
import numpy as np
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from data.loader import split_602020

def screening(p):
    train,_,_=split_602020(p)
    x=train.to_numpy(dtype=float)
    corr=float(train.corr().iloc[0,1])
    eg_p=float(coint(x[:,0],x[:,1],trend='c',autolag='aic')[1])
    j=coint_johansen(x,det_order=0,k_ar_diff=2)
    trace_rank=int(sum(j.lr1>j.cvt[:,1]))
    eigen_rank=int(sum(j.lr2>j.cvm[:,1]))
    beta=j.evec[:,0].copy();beta=beta/beta[0]
    if beta[0]<0:beta=-beta
    spread=x@beta
    adf_p=float(adfuller(spread,regression='c',autolag='aic')[1])
    dp=np.diff(spread); lag=spread[:-1]; b=np.polyfit(lag,dp,1)[0]
    half_life=float(-np.log(2)/np.log(1+b)) if 0<1+b<1 else float('nan')
    i1 = all(adfuller(x[:,i],regression='c',autolag='aic')[1]>.05 and adfuller(np.diff(x[:,i]),regression='c',autolag='aic')[1]<.05 for i in range(2))
    passed=bool(corr>.7 and eg_p<.05 and trace_rank==1 and eigen_rank==1 and i1 and adf_p<.05)
    return {'correlation':corr,'engle_granger_p':eg_p,'johansen_trace_rank':trace_rank,
      'johansen_eigen_rank':eigen_rank,'adf_spread_diagnostic_p':adf_p,
      'i1_indicative':bool(i1),'half_life_train':half_life,'screen_pass':passed,
      'beta_train':beta.tolist(),'train_end':str(train.index[-1].date())}


def rolling_johansen(prices, window=504, step=21, k_ar_diff=2, det_order=0):
    """Diagnóstico causal de Johansen en ventana móvil.

    En cada fecha t utiliza únicamente observaciones <= t, sin mirar al futuro.
    NO genera señales ni selecciona parámetros según test/validación.
    beta_a = 1 es la convención de escala; beta_b se alinea por ese signo.
    Si una ventana falla, se registra el error sin fabricar un vector.
    """
    import pandas as pd

    if window <= k_ar_diff + 10 or step < 1:
        raise ValueError('Ventana insuficiente o paso inválido')
    arr = np.asarray(prices, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError('Se requieren exactamente dos columnas de precios')
    idx = prices.index if hasattr(prices, 'index') else pd.RangeIndex(len(arr))
    cols = ['beta_a', 'beta_b', 'trace_rank', 'eigen_rank', 'trace_r0', 'trace_r1', 'error']
    rows = []
    for end in range(window-1, len(arr), step):
        sample = arr[end-window+1:end+1]
        row = dict(date=idx[end], beta_a=np.nan, beta_b=np.nan,
                   trace_rank=np.nan, eigen_rank=np.nan,
                   trace_r0=np.nan, trace_r1=np.nan, error='')
        if not np.isfinite(sample).all():
            row['error'] = 'Precios no finitos en ventana'
        else:
            try:
                j = coint_johansen(sample, det_order=det_order, k_ar_diff=k_ar_diff)
                v = j.evec[:, 0].astype(float)
                if np.isfinite(v).all() and abs(v[0]) > 1e-12:
                    v = v / v[0]
                    row.update(beta_a=float(v[0]), beta_b=float(v[1]),
                               trace_rank=int(sum(j.lr1 > j.cvt[:, 1])),
                               eigen_rank=int(sum(j.lr2 > j.cvm[:, 1])),
                               trace_r0=float(j.lr1[0]), trace_r1=float(j.lr1[1]))
                else:
                    row['error'] = 'Vector no normalizable'
            except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
                row['error'] = f'{type(exc).__name__}: {str(exc)[:140]}'
        rows.append(row)
    return pd.DataFrame(rows, columns=['date'] + cols).set_index('date')
