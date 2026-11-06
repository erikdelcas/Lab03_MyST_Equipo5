"""Filtros recursivos causales: cobertura y media/log-varianza de una senal.

Kalman 2: dos estados escalares aleatorios (media y log-varianza).
La medicion de log-varianza es una pseudo-observacion de la innovacion
cuadratica, con correccion por sesgo de log(chi-cuadrado_1).
No es un filtro gaussiano lineal conjunto de media y varianza: es una
aproximacion de dos filtros de Kalman acoplados y debe declararse asi.
"""
import numpy as np


def hedge_filter(prices, q=1e-5, r=4.0, initial_hedge=1., burn_in=30):
    """P_A,t = c_t+h_t P_B,t+eps_t; beta=(1,-h_t); actualizacion causal."""
    x = np.array([0., float(initial_hedge)])
    P = np.eye(2) * 100.
    Q = np.eye(2) * q
    bets, gains, uncertainties = [], [], []
    for pa, pb in np.asarray(prices, dtype=float):
        P = P + Q
        H = np.array([1., pb])
        v = float(r + H @ P @ H)
        K = P @ H / v
        innovation = float(pa - H @ x)
        x = x + K * innovation
        P = ((np.eye(2) - np.outer(K, H)) @ P
             @ (np.eye(2) - np.outer(K, H)).T + np.outer(K, K) * r)
        bets.append([1., -float(x[1])])
        gains.append(K.tolist())
        uncertainties.append(float(np.trace(P)))
    bets = np.asarray(bets)
    spreads = np.sum(bets * np.asarray(prices), axis=1)
    spreads[:burn_in] = np.nan
    return {'beta': bets, 'spread': spreads, 'gain': np.asarray(gains),
            'variance': np.asarray(uncertainties)}


def signal_filter(values, q=1e-4, r=.01, burn_in=30,
                  q_logvar=0.01, r_logvar=np.pi**2/2, min_variance=1e-8):
    """Predice y actualiza dos estados latentes: media y log-varianza.

    Modelo: mu_t = mu_(t-1) + w_mu; ell_t = ell_(t-1) + w_ell,
    ell_t=log(sigma_t^2), y_t = mu_t + epsilon_t.
    Actualizacion media: Kalman escalar con r.
    Pseudo-medicion para log-varianza: log((y-mu_pred)^2 + eps)
    - E[log(chi2_1)] ~ ell_t + ruido, varianza aprox pi^2/2.
    Es una aproximacion de Kalman acoplada, no un EKF exacto.
    El z-score usa exclusivamente predicciones anteriores a observar y_t.
    """
    vals = np.asarray(values, dtype=float)
    if vals.ndim != 1 or q < 0 or r <= 0 or q_logvar < 0 or r_logvar <= 0 or min_variance <= 0:
        raise ValueError('Dimensiones o parametros de Kalman 2 invalidos')
    m, pm = 0., 1.
    ell, pe = 0., 1.
    # Euler-Mascheroni + log(2) = -E[log(chi^2_1)]
    log_chi2_bias = 1.2703628454614782
    zs, means, sigmas, gains, post_var = [], [], [], [], []
    logvar_pred, var_pred, gain_var, logvar_post, var_state_unc = [], [], [], [], []
    for i, y in enumerate(vals):
        pm_predict = pm + q
        pe_predict = pe + q_logvar
        v_predict = max(float(np.exp(np.clip(ell, -35., 35.))), min_variance)
        # Predictivo: incertidumbre del estado de media + ruido latente.
        sigma = float(np.sqrt(v_predict + pm_predict))
        means.append(float(m))
        sigmas.append(sigma)
        logvar_pred.append(float(ell))
        var_pred.append(v_predict)
        z = ((float(y) - m) / sigma) if np.isfinite(y) and i >= burn_in else np.nan
        zs.append(z)
        if np.isfinite(y):
            innovation = float(y - m)
            # La primera ecuacion conserva la parametrizacion q,r existente.
            km = pm_predict / (pm_predict + r)
            m += km * innovation
            pm = (1. - km) * pm_predict
            # Transformacion log de la innovacion al cuadrado, ajustada por sesgo.
            pseudo = float(np.log(innovation**2 + min_variance) + log_chi2_bias)
            kv = pe_predict / (pe_predict + r_logvar)
            ell += kv * (pseudo - ell)
            ell = float(np.clip(ell, -35., 35.))
            pe = (1. - kv) * pe_predict
        else:
            km, kv = 0., 0.
            pm, pe = pm_predict, pe_predict
        gains.append(float(km))
        gain_var.append(float(kv))
        post_var.append(float(pm))
        logvar_post.append(float(ell))
        var_state_unc.append(float(pe))
    return {'z': np.asarray(zs), 'predictive_mean': np.asarray(means),
            'predictive_sigma': np.asarray(sigmas), 'gain': np.asarray(gains),
            'posterior_variance': np.asarray(post_var),
            'predictive_log_variance': np.asarray(logvar_pred),
            'predictive_variance': np.asarray(var_pred),
            'variance_gain': np.asarray(gain_var),
            'posterior_log_variance': np.asarray(logvar_post),
            'variance_state_uncertainty': np.asarray(var_state_unc)}
