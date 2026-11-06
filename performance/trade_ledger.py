"""Reconstrucción causal de operaciones (episodios) desde posiciones ejecutadas.

No recalcula señales ni el backtest. P&L bruto = P&L por movimiento de precios
sobre posiciones que existían ANTES del cierre; costos efectivos del CSV.
Cada inversión de dirección cierra un episodio y abre otro.
"""
import numpy as np
import pandas as pd


COLUMNS = ['trade_id','entry_date','exit_date','status','direction','entry_partition',
           'exit_partition','holding_days','entry_gross_notional','gross_pnl',
           'commissions','borrow_cost','net_pnl','net_return_on_entry_gross',
           'entry_equity','exit_equity','rebalance_days']


def build_trade_ledger(bt, *, atol=1e-5):
    required = ['shares_a','shares_b','price_a','price_b','commission','borrow','equity']
    missing = [x for x in required if x not in bt.columns]
    if missing:
        raise ValueError('Columnas faltantes: ' + ', '.join(missing))
    if bt.empty:
        return pd.DataFrame(columns=COLUMNS)
    if not bt.index.is_monotonic_increasing or bt.index.has_duplicates:
        raise ValueError('Índice de fechas debe estar ordenado sin duplicados')
    a = bt[required].astype(float)
    if not np.isfinite(a.to_numpy()).all():
        raise ValueError('Valores no finitos en columnas financieras')
    positions = a[['shares_a','shares_b']].to_numpy(dtype=float)
    px = a[['price_a','price_b']].to_numpy(dtype=float)
    if (px<=0).any():
        raise ValueError('Precios no positivos')
    fees = a['commission'].to_numpy(dtype=float)
    loans = a['borrow'].to_numpy(dtype=float)
    equity = a['equity'].to_numpy(dtype=float)
    if (fees < 0).any() or (loans < 0).any():
        raise ValueError('Costos negativos')
    active = None
    completed=[]

    def new_trade(t, charge=0.):
        nonlocal active
        pos = positions[t]
        p=px[t]
        gross = float(np.abs(pos*p).sum())
        if gross<=0: return
        active={
            'trade_id':len(completed)+1,
            'entry_date': bt.index[t], 'exit_date':pd.NaT, 'status':'abierta',
            'direction':'spread_largo' if pos[0]>0 else 'spread_corto',
            'entry_partition':str(bt.iloc[t]['partition']) if 'partition' in bt.columns else 'sin_etiqueta',
            'exit_partition':'', 'holding_days':0,
            'entry_gross_notional':gross,
            'gross_pnl':0.,'commissions':float(charge), 'borrow_cost':0.,
            'net_pnl':0., 'net_return_on_entry_gross':0.,
            'entry_equity':float(equity[t]+charge), 'exit_equity':np.nan,
            'rebalance_days':0,
        }

    def close(t):
        nonlocal active
        active['exit_date']=bt.index[t]
        active['exit_partition']=str(bt.iloc[t]['partition']) if 'partition' in bt.columns else 'sin_etiqueta'
        active['status']='cerrada'
        finish()

    def finish():
        nonlocal active
        active['net_pnl']=float(active['gross_pnl']-active['commissions']-active['borrow_cost'])
        active['net_return_on_entry_gross']=active['net_pnl']/active['entry_gross_notional'] if active['entry_gross_notional'] else np.nan
        completed.append(active)
        active=None

    for t in range(len(bt)):
        prev=positions[t-1] if t else np.zeros(2)
        curr=positions[t]
        p=px[t]
        prev_p=px[t-1] if t else p
        prev_live=bool(np.any(prev))
        curr_live=bool(np.any(curr))
        changed_direction = prev_live and curr_live and (np.sign(prev[0]) != np.sign(curr[0]))
        gross_day=float(prev@(p-prev_p))
        if prev_live:
            if active is None:
                raise AssertionError('Episodio previo no identificado')
            active['gross_pnl']+=gross_day
            active['borrow_cost']+=float(loans[t])
            active['holding_days']+=1
        elif loans[t]>atol:
            raise ValueError('Costo de préstamo sin posición previa')
        if changed_direction:
            # Cada pata se cierra y se reabre: por linealidad, la comisión se
            # distribuye usando su exposición absoluta al cierre actual.
            closing_turn=float(np.abs(prev*p).sum())
            opening_turn=float(np.abs(curr*p).sum())
            total=closing_turn+opening_turn
            exit_charge=float(fees[t]*closing_turn/total)
            entry_charge=float(fees[t]-exit_charge)
            active['commissions']+=exit_charge
            close(t)
            new_trade(t,entry_charge)
        elif prev_live and not curr_live:
            active['commissions']+=float(fees[t])
            close(t)
        elif not prev_live and curr_live:
            new_trade(t,float(fees[t]))
        elif prev_live and curr_live:
            active['commissions']+=float(fees[t])
            if np.any(curr!=prev): active['rebalance_days']+=1
        elif fees[t]>atol:
            raise ValueError('Comisión sin transacción ni posición')

    if active is not None:
        active['exit_date']=pd.NaT
        active['exit_partition']=str(bt.iloc[-1]['partition']) if 'partition' in bt.columns else 'sin_etiqueta'
        active['exit_equity']=float(equity[-1])
        finish()
    ledger = pd.DataFrame(completed,columns=COLUMNS)
    # Reconciliación contra contabilidad ejecutada, no aproximación.
    ledger_net = float(ledger.net_pnl.sum()) if not ledger.empty else 0.
    equity_delta = float(equity[-1]-(equity[0]+fees[0]))
    if not np.isclose(ledger_net,equity_delta,rtol=0,atol=max(atol,abs(equity_delta)*1e-9)):
        raise ValueError(f'P&L no reconcilia: operaciones {ledger_net:.5f} vs equity {equity_delta:.5f}. Revisar el CSV.')
    return ledger
