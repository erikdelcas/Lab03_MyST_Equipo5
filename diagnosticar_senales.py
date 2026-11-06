"""Compara una regla alternativa de señales con el backtest guardado.
No cambia el proyecto original ni ajusta parámetros con datos fuera de entrenamiento.
Ejecutar desde la raíz del proyecto: python diagnosticar_senales.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from backtest.engine import simulate
from config import CFG


def positions_rearm(z, entry=2.0, exit=0.5, stop=4.0, max_hold=45):
    """Variante exploratoria: no entrar ante saltos más allá del stop;
    tras salir por stop o límite temporal, esperar a regresar a la zona neutral.
    La decisión al cierre t se ejecuta en t+1 por simulate.
    """
    z = np.asarray(z, dtype=float)
    out = np.zeros(len(z), dtype=int)
    position, age, armed = 0, 0, True
    for t, v in enumerate(z):
        if not np.isfinite(v):
            position, age, armed = 0, 0, False
        elif position == 0:
            if abs(v) < exit:
                armed = True
            if armed and entry <= abs(v) < stop:
                position = -1 if v > 0 else 1
                age = 0
                armed = False
        else:
            age += 1
            reason = (abs(v) < exit, abs(v) > stop, age >= max_hold)
            if any(reason):
                position, age = 0, 0
                armed = bool(reason[0])
        out[t] = position
    return out


def summarize(bt):
    commission = float(bt['commission'].sum())
    borrow = float(bt['borrow'].sum())
    net = float(bt['equity'].iloc[-1] - bt['equity'].iloc[0])
    pos = bt['position'].astype(int)
    opens = int(((pos != 0) & (pos.shift(fill_value=0) == 0)).sum())
    flips = int(((pos != 0) & (pos.shift(fill_value=0) * pos < 0)).sum())
    return {'entradas': opens + flips, 'dias_con_operacion': int((bt.trade_notional > 0).sum()),
            'comisiones': round(commission, 2), 'prestamo': round(borrow, 2),
            'resultado_bruto_aprox': round(net + commission + borrow, 2),
            'resultado_neto': round(net, 2), 'equity_final': round(float(bt.equity.iloc[-1]), 2)}


def main():
    path = Path('artifacts/GOOG_GOOGL_backtest.csv')
    if not path.exists():
        raise FileNotFoundError('No se encontró artifacts/GOOG_GOOGL_backtest.csv')
    saved = pd.read_csv(path, parse_dates=['date']).set_index('date')
    alt_signal = positions_rearm(saved['kalman2_z'], CFG.entry_z, CFG.exit_z,
                                 CFG.stop_z, CFG.max_hold)
    prices = saved[['price_a', 'price_b']]
    betas = saved[['beta_a', 'beta_b']].to_numpy()
    alt = simulate(prices, betas, alt_signal, CFG.initial_capital,
                   CFG.max_gross_fraction, CFG.fee, CFG.annual_borrow)
    original_sim = simulate(prices, betas, saved['signal'].to_numpy(),
                            CFG.initial_capital, CFG.max_gross_fraction,
                            CFG.fee, CFG.annual_borrow)
    if not np.allclose(original_sim.equity, saved.equity, atol=0.01):
        print('ADVERTENCIA: el backtest de referencia no se reprodujo exactamente.')
    result = pd.DataFrame({'Original': summarize(saved), 'Variante_rearme': summarize(alt)})
    print('\nCOMPARACIÓN DESCRIPTIVA — NO CONSTITUYE OPTIMIZACIÓN NI VALIDACIÓN')
    print(result.to_string())
    out = Path('artifacts/comparacion_senales_exploratoria.csv')
    result.to_csv(out)
    print('\nArchivo generado:', out)
    print('ATENCIÓN: comparar en entrenamiento antes de seleccionar una política;')
    print('no escoger la variante por sus resultados en test o validación.')

if __name__ == '__main__':
    main()
