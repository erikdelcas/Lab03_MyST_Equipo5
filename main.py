"""Ejecutar: python main.py. Requiere conexión la primera vez para precios."""
import json
import numpy as np
import pandas as pd
from config import ROOT, PAIRS, CFG, SEED, JUSTIFICATION
from data.loader import get_prices,split_602020
from cointegration.screen import screening, rolling_johansen
from kalman.filters import hedge_filter,signal_filter
from strategy.vecm_signals import vecm_innovations_dynamic,positions_from_z
from backtest.engine import simulate
from performance.metrics import evaluate

def run():
    np.random.seed(SEED)
    output=ROOT/'artifacts'; output.mkdir(exist_ok=True)
    names=list(dict.fromkeys(x for pair in PAIRS.values() for x in pair))
    prices=get_prices(names)
    summaries=[]
    for name,(a,b) in PAIRS.items():
        p=prices[[a,b]].dropna();train,test,valid=split_602020(p)
        diagnostic=screening(p)
        if CFG.strict_cointegration and not diagnostic['screen_pass']:
            print(name,'descartado por filtro estricto');continue
        h0=-diagnostic['beta_train'][1]
        filt1=hedge_filter(p.values,CFG.kalman_q_hedge,CFG.kalman_r_hedge,h0)
        # Se usa beta[t-1] para proyectar la innovacion observada en t:
        # coincide con los pesos decididos para la ejecucion al cierre siguiente.
        errors, errors_fixed, vecm, beta = vecm_innovations_dynamic(
            p.values,len(train),filt1['beta'],k=2)
        filt2=signal_filter(errors,CFG.kalman_q_mean,CFG.kalman_r_mean)
        # La referencia fija se registra como diagnostico; no se escoge
        # una senal segun el rendimiento de test/validation.
        fixed_z=signal_filter(errors_fixed,CFG.kalman_q_mean,CFG.kalman_r_mean)['z']
        decisions=positions_from_z(filt2['z'],CFG.entry_z,CFG.exit_z,CFG.stop_z,CFG.max_hold)
        # El VECM y beta inicial se estiman con todo TRAIN.
        # Por ello NO evaluamos operaciones dentro de TRAIN: hacerlo usaría
        # parámetros estimados con datos posteriores a esas operaciones.
        decisions_raw=decisions.copy()
        decisions[:len(train)]=0
        bt=simulate(p,filt1['beta'],decisions,CFG.initial_capital,CFG.max_gross_fraction,CFG.fee,CFG.annual_borrow)
        assert (bt.iloc[:len(train)]['trade_notional']==0).all(), 'Operaciones en entrenamiento: posible look-ahead'
        bt['price_a']=p.iloc[:,0];bt['price_b']=p.iloc[:,1]
        bt['spread_dynamic']=filt1['spread'];bt['beta_a']=filt1['beta'][:,0];bt['beta_b']=filt1['beta'][:,1]
        bt['kalman1_gain_a']=filt1['gain'][:,0];bt['kalman1_gain_b']=filt1['gain'][:,1]
        bt['kalman1_uncertainty']=filt1['variance'];bt['vecm_residual']=errors
        bt['vecm_residual_fixed']=errors_fixed; bt['kalman2_z_fixed_diagnostic']=fixed_z
        bt['kalman2_z']=filt2['z'];bt['kalman2_mean_pre']=filt2['predictive_mean']
        bt['kalman2_sigma_pre']=filt2['predictive_sigma'];bt['kalman2_gain']=filt2['gain']
        bt['kalman2_uncertainty']=filt2['posterior_variance'];bt['signal']=decisions;bt['signal_exploratoria_train']=decisions_raw
        bt['partition']=np.where(np.arange(len(bt))<len(train),'train',np.where(np.arange(len(bt))<len(train)+len(test),'test','validation'))
        # Johansen móvil solo para diagnóstico y visualización; jamás cambia las señales.
        rolling = rolling_johansen(p, window=504, step=21, k_ar_diff=2, det_order=0)
        rolling.to_csv(output/f'{name}_johansen_movil.csv', index_label='date')
        bt.to_csv(output/f'{name}_backtest.csv',index_label='date')
        # Métricas de inversión únicamente fuera de muestra (test + validation).
        bt_oos=bt.iloc[len(train):].copy()
        bt_oos['drawdown']=bt_oos.equity/bt_oos.equity.cummax()-1.
        score=evaluate(bt_oos)
        summaries.append({'pair':name,'economic_logic':JUSTIFICATION[name],**diagnostic,**score})
        print(f'{name}: train={len(train)} test={len(test)} validation={len(valid)} | screening={diagnostic["screen_pass"]} | Sharpe OOS={score["sharpe"]:.3f}')
    if not summaries: raise RuntimeError('Ningún par superó los filtros; revisar diagnóstico')
    pd.DataFrame(summaries).to_csv(output/'metrics.csv',index=False)
    (output/'config_used.json').write_text(json.dumps(CFG.__dict__,indent=2),encoding='utf-8')
    print('Archivos creados en:',output)
if __name__=='__main__':run()
