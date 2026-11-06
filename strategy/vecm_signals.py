"""Modelo VECM ajustado SOLO en entrenamiento; innovaciones fuera de muestra con coeficientes congelados."""
import numpy as np
from statsmodels.tsa.vector_ar.vecm import VECM

def vecm_innovations(prices,train_len,k=2):
    p=np.asarray(prices,dtype=float)
    if train_len<max(100,k+20):raise ValueError('Entrenamiento insuficiente')
    fit=VECM(p[:train_len],k_ar_diff=k,coint_rank=1,deterministic='n').fit()
    beta=fit.beta[:,0].copy(); beta/=beta[0]
    gamma=fit.gamma
    out=np.full(len(p),np.nan)
    for t in range(k+1,len(p)):
        ect=(fit.alpha@(fit.beta.T@p[t-1]))
        lags=np.concatenate([p[t-i]-p[t-i-1] for i in range(1,k+1)])
        pred=ect+gamma@lags
        err=(p[t]-p[t-1])-pred
        out[t]=float(beta@err)
    return out,fit,beta

def vecm_innovations_dynamic(prices, train_len, beta_lagged, k=2):
    """Proyecta innovaciones VECM sobre beta Kalman disponible en t-1.

    El VECM se ajusta SOLO con entrenamiento y queda congelado. El componente
    de correccion de error del VECM sigue utilizando su beta de entrenamiento.
    Esta proyeccion adapta la DIRECCION del error usado como senal a la misma
    direccion empleada para formar las posiciones. NO equivale a reestimar un
    VECM con cointegracion dinamica y NO valida cointegracion fuera de muestra.
    """
    p = np.asarray(prices, dtype=float)
    weights = np.asarray(beta_lagged, dtype=float)
    if p.shape != weights.shape or p.ndim != 2 or p.shape[1] != 2:
        raise ValueError('prices y beta_lagged deben ser arreglos (n,2)')
    if train_len < max(100, k + 20) or train_len > len(p):
        raise ValueError('Entrenamiento insuficiente o invalido')
    fit = VECM(p[:train_len], k_ar_diff=k, coint_rank=1, deterministic='n').fit()
    # FIX: usar alpha @ (beta.T @ P_{t-1}) como ajuste del cambio condicional.
    out = np.full(len(p), np.nan)
    fixed = np.full(len(p), np.nan)
    fitted_beta = fit.beta[:, 0].copy()
    fitted_beta = fitted_beta / fitted_beta[0]
    for t in range(k + 1, len(p)):
        ect = fit.alpha @ (fit.beta.T @ p[t-1])
        lags = np.concatenate([p[t-i]-p[t-i-1] for i in range(1,k+1)])
        pred = ect + fit.gamma @ lags
        residual = (p[t]-p[t-1]) - pred
        if np.all(np.isfinite(weights[t-1])):
            out[t] = float(weights[t-1] @ residual)
        fixed[t] = float(fitted_beta @ residual)
    return out, fixed, fit, fitted_beta

def positions_from_z(z,entry=2.,exit=.5,stop=4.,max_hold=45):
    """Decisión al cierre t; ejecución en siguiente cierre dentro del backtest."""
    result=np.zeros(len(z),dtype=int); pos=0; age=0
    for t,v in enumerate(z):
        if not np.isfinite(v):pos=0;age=0
        elif pos==0:
            if v<=-entry:pos=1;age=0
            elif v>=entry:pos=-1;age=0
        else:
            age+=1
            if abs(v)<exit or abs(v)>stop or age>=max_hold:pos=0;age=0
        result[t]=pos
    return result
