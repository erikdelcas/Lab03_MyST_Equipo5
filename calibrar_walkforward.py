"""Calibración de umbrales SOLO dentro del 60% de entrenamiento.

No modifica main.py ni los backtests existentes. Separación:
- Inner walk-forward: expanding fits y validaciones cronológicas dentro del TRAIN.
- Outer test / validation: evaluación posterior con parámetros congelados.
Los pares ya fueron preseleccionados anteriormente; esta herramienta NO corrige
el sesgo potencial por búsqueda múltiple de pares.
"""
from pathlib import Path
import numpy as np
import pandas as pd

from config import ROOT, PAIRS, CFG
from data.loader import get_prices, split_602020
from kalman.filters import hedge_filter, signal_filter
from strategy.vecm_signals import vecm_innovations_dynamic, positions_from_z
from backtest.engine import simulate

# Grid fijado ANTES de observar el desempeño OOS.
GRID = [(entry, exit_) for entry in (1.5, 2.0, 2.5)
        for exit_ in (0.25, 0.5) if exit_ < entry]
FOLD_EDGES = ((0.45, 0.60), (0.60, 0.75), (0.75, 0.90), (0.90, 1.00))
MIN_TRADES_TOTAL = 8


def inner_folds(n_train):
    """(fin_estimacion, fin_validacion), índices exclusivos; sin solapamiento."""
    if n_train < 600:
        raise ValueError('Entrenamiento demasiado corto para walk-forward')
    folds = [(int(n_train * a), int(n_train * b)) for a, b in FOLD_EDGES]
    if any(a < 100 or b <= a for a, b in folds):
        raise ValueError('Folds inválidos')
    return folds


def _signals_for_fit(prices, fit_end):
    """Ajusta VECM hasta fit_end; estados Kalman causales hasta cada fecha.

    Los parámetros del filtro son los de config.py. Inicialización hedge de OLS
    sobre la submuestra de ajuste (jamás sobre validación/test).
    """
    px = np.asarray(prices, dtype=float)
    x = px[:fit_end]
    slope = float(np.polyfit(x[:, 1], x[:, 0], 1)[0])
    hedge = hedge_filter(px, CFG.kalman_q_hedge, CFG.kalman_r_hedge,
                         initial_hedge=slope)
    residual, _, _, _ = vecm_innovations_dynamic(px, fit_end, hedge['beta'], k=2)
    z = signal_filter(residual, CFG.kalman_q_mean, CFG.kalman_r_mean)['z']
    return z, hedge['beta']


def _simulate_forward(prices, z, beta, start, end, entry, exit_):
    """Sin operar antes de start; analiza solamente [start,end)."""
    dec = positions_from_z(z[:end], entry=entry, exit=exit_,
                           stop=CFG.stop_z, max_hold=CFG.max_hold)
    dec[:start] = 0
    # El último cierre genera señal para ejecución futura; fuera del fold se omite.
    bt = simulate(prices.iloc[:end], beta[:end], dec,
                  CFG.initial_capital, CFG.max_gross_fraction,
                  CFG.fee, CFG.annual_borrow)
    relevant = bt.iloc[start:end]
    initial = float(bt.equity.iloc[start - 1]) if start else CFG.initial_capital
    final = float(bt.equity.iloc[end - 1])
    equity = np.r_[initial, relevant.equity.to_numpy(dtype=float)]
    dd = equity / np.maximum.accumulate(equity) - 1
    return {
        'return_net': final / initial - 1.0,
        'max_dd': float(dd.min()),
        'commission': float(relevant.commission.sum()),
        'borrow': float(relevant.borrow.sum()),
        'trade_days': int((relevant.trade_notional > 0).sum()),
        'entry_days': int((relevant.trade_event == 'entrada').sum()),
        'capital_final': final,
    }


def _score_fold(net, dd):
    # Objetivo predeterminado, financiero y consistente entre folds.
    return float(net - .25 * abs(dd))


def select_by_inner_folds(rows):
    """Selecciona una política por mediana de utilidad, penalizando inactividad.
    Si ninguna alcanza MIN_TRADES_TOTAL, devuelve baseline sin pretensión de óptimo.
    """
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError('Faltan validaciones internas')
    ranked = (frame.groupby(['entry_z', 'exit_z'], as_index=False)
              .agg(median_objective=('objective', 'median'),
                   total_entries=('entry_days', 'sum'),
                   folds=('fold', 'nunique')))
    ranked['eligible'] = ((ranked.total_entries >= MIN_TRADES_TOTAL)
                          & (ranked.folds == len(FOLD_EDGES)))
    eligible = ranked[ranked.eligible]
    if eligible.empty:
        return (float(CFG.entry_z), float(CFG.exit_z), 'baseline_no_elegibles'), ranked
    best = eligible.sort_values(['median_objective', 'entry_z', 'exit_z'],
                                ascending=[False, True, True]).iloc[0]
    return (float(best.entry_z), float(best.exit_z), 'seleccion_interna'), ranked


def run():
    output = ROOT / 'artifacts'
    output.mkdir(parents=True, exist_ok=True)
    tickers = list(dict.fromkeys(t for pair in PAIRS.values() for t in pair))
    data = get_prices(tickers)
    fold_rows, selection_rows, oos_rows = [], [], []
    for name, (a, b) in PAIRS.items():
        p = data[[a, b]].dropna()
        train, test, validation = split_602020(p)
        n_train = len(train)
        cached = []
        for i, (fit_end, val_end) in enumerate(inner_folds(n_train), 1):
            sub = p.iloc[:val_end]
            z, beta = _signals_for_fit(sub.to_numpy(), fit_end)
            cached.append((i, fit_end, val_end, sub, z, beta))
        rows_pair = []
        for entry, exit_ in GRID:
            for fold, fit_end, val_end, sub, z, beta in cached:
                r = _simulate_forward(sub, z, beta, fit_end, val_end, entry, exit_)
                item = {'pair': name, 'fold': fold,
                        'fit_end_date': str(p.index[fit_end - 1].date()),
                        'validation_start': str(p.index[fit_end].date()),
                        'validation_end': str(p.index[val_end - 1].date()),
                        'entry_z': entry, 'exit_z': exit_, **r}
                item['objective'] = _score_fold(r['return_net'], r['max_dd'])
                rows_pair.append(item)
        fold_rows.extend(rows_pair)
        (entry, exit_, status), ranking = select_by_inner_folds(rows_pair)
        ranking.insert(0, 'pair', name)
        selection_rows.extend(ranking.to_dict('records'))
        # Evaluación OUTER usando exclusivamente parámetros seleccionados dentro de TRAIN.
        z_full, beta_full = _signals_for_fit(p.to_numpy(), n_train)
        # Congelar la política y evaluar test y validation de manera continua.
        for label, en, ex in [('baseline', float(CFG.entry_z), float(CFG.exit_z)),
                              ('seleccion_train', entry, exit_)]:
            decisions = positions_from_z(z_full, en, ex, CFG.stop_z, CFG.max_hold)
            decisions[:n_train] = 0
            bt = simulate(p, beta_full, decisions, CFG.initial_capital,
                          CFG.max_gross_fraction, CFG.fee, CFG.annual_borrow)
            for partition, start, end in [('test', n_train, n_train + len(test)),
                                          ('validation', n_train + len(test), len(p))]:
                segment = bt.iloc[start:end]
                start_equity = float(bt.equity.iloc[start - 1])
                equity_path = np.r_[start_equity, segment.equity.to_numpy(dtype=float)]
                dd = equity_path / np.maximum.accumulate(equity_path) - 1
                r = segment['return'].to_numpy(dtype=float)
                stdev = np.std(r, ddof=1) if len(r) > 1 else 0.0
                oos_rows.append({'pair': name, 'policy': label,
                                 'partition': partition, 'entry_z': en, 'exit_z': ex,
                                 'selection_status': status,
                                 'return_net': float(equity_path[-1] / equity_path[0] - 1),
                                 'max_dd': float(dd.min()),
                                 'sharpe': float(np.mean(r)/stdev*np.sqrt(252)) if stdev > 0 else np.nan,
                                 'commission': float(segment.commission.sum()),
                                 'borrow': float(segment.borrow.sum()),
                                 'trade_days': int((segment.trade_notional > 0).sum())})
        print(f'{name}: entry={entry:g}, exit={exit_:g}; {status}. '
              'Test/validation NO utilizados para elegir.')
    pd.DataFrame(fold_rows).to_csv(output / 'walkforward_folds_train.csv', index=False)
    pd.DataFrame(selection_rows).to_csv(output / 'walkforward_grid_train.csv', index=False)
    pd.DataFrame(oos_rows).to_csv(output / 'walkforward_oos_comparison.csv', index=False)
    print('CSV generados en', output)
    print('Aviso: pares exploratorios, cointegración no confirmada fuera de muestra.')


if __name__ == '__main__':
    run()
