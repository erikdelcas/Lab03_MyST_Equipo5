"""Comparación descriptiva de rebalanceo diario versus banda fija usando artifacts/*_backtest.csv.
Ejecutar desde raíz del proyecto: python comparar_rebalanceo.py
NO optimiza una banda sobre test/validación ni reentrena señales.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from backtest.engine import simulate
from config import CFG, PAIRS, ROOT

BAND = 0.02  # decisión EX ANTE: no rebalancear si ajuste < 2% de exposición objetivo
OUT = ROOT / 'artifacts'


def run():
    all_rows = []
    for pair in PAIRS:
        path = OUT / f'{pair}_backtest.csv'
        if not path.exists():
            raise FileNotFoundError(f'Falta {path}. Ejecuta primero python main.py')
        df = pd.read_csv(path, parse_dates=['date']).set_index('date')
        cols = ['price_a', 'price_b', 'beta_a', 'beta_b', 'signal', 'partition']
        absent = [c for c in cols if c not in df]
        if absent:
            raise ValueError(f'{pair}: faltan columnas {absent}')
        px = df[['price_a', 'price_b']]
        beta = df[['beta_a', 'beta_b']].to_numpy(dtype=float)
        decisions = df['signal'].fillna(0).to_numpy(dtype=int)
        # El entrenamiento permanece sin operar. La primera orden OOS puede ejecutarse
        # en el cierre siguiente, como en el motor del proyecto.
        decisions[df['partition'].eq('train').to_numpy()] = 0
        cfg = dict(capital=CFG.initial_capital, gross_limit=CFG.max_gross_fraction,
                   fee=CFG.fee, borrow=CFG.annual_borrow)
        daily = simulate(px, beta, decisions, **cfg, rebalance_band=0)
        band = simulate(px, beta, decisions, **cfg, rebalance_band=BAND)
        for name, bt in [('diario', daily), ('banda_2pct', band)]:
            bt = bt.copy()
            bt['partition'] = df['partition']
            bt['policy'] = name
            bt.to_csv(OUT / f'{pair}_rebalance_{name}.csv', index_label='date')
            oos = bt[bt['partition'].isin(['test', 'validation'])]
            if len(oos) == 0:
                raise ValueError('No hay periodo fuera de entrenamiento')
            ret = oos['return'].to_numpy(float)
            vol = np.std(ret, ddof=1) if len(ret)>1 else np.nan
            sharpe = float(np.mean(ret)/vol*np.sqrt(252)) if vol and np.isfinite(vol) else np.nan
            # Base de capital inicial = ultima marca del entrenamiento, porque no se opera ahi.
            initial = bt.loc[bt['partition'].eq('train'), 'equity'].iloc[-1]
            all_rows.append(dict(pair=pair, policy=name, band=BAND if name!='diario' else 0,
                capital_inicio_oos=initial, capital_final=float(bt['equity'].iloc[-1]),
                pnl_neto_oos=float(bt['equity'].iloc[-1]-initial),
                comisiones_oos=float(oos['commission'].sum()),
                comisiones_rebalance_oos=float(oos['commission_rebalance'].sum()),
                comisiones_entrada_salida_oos=float(oos['commission_entry_exit'].sum()),
                prestamo_oos=float(oos['borrow'].sum()),
                dias_con_transaccion=int((oos['trade_notional']>0).sum()),
                ajustes_omitidos=int(oos['rebalance_skipped'].sum()),
                sharpe_oos=sharpe,
                limite_80pct_cumplido=bool((bt['gross_exposure'] <= CFG.max_gross_fraction * bt['equity'] + 1e-6).all()),
            ))
    summary = pd.DataFrame(all_rows)
    destination = OUT / 'comparacion_rebalanceo.csv'
    summary.to_csv(destination, index=False)
    print('\nCOMPARACIÓN DESCRIPTIVA (test + validación, NO optimización)')
    print(summary[['pair','policy','capital_final','comisiones_oos','comisiones_rebalance_oos','dias_con_transaccion','ajustes_omitidos','sharpe_oos','limite_80pct_cumplido']].to_string(index=False))
    print('\nGuardado:', destination)
    return summary

if __name__ == '__main__':
    run()
