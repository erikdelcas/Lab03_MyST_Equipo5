"""Backtest de dos patas, con ejecución al cierre siguiente y control de exposición.

La decisión del cierre t-1 se ejecuta al precio de cierre t. El patrimonio al
cierre t incorpora los movimientos de precio previos a ejecutar, el costo de
préstamo diario y las comisiones. No estima el desempeño de una estrategia.
"""
import numpy as np
import pandas as pd


def simulate(prices, beta, decisions, capital=1e6, gross_limit=.8,
             fee=.00125, borrow=.0025, rebalance_band=0.0):
    """Simula dos patas en acciones enteras sin superar el límite bruto.

    Conserva la interfaz y columnas de la versión inicial; añade columnas
    descriptivas de eventos y costos. Las posiciones cortas presuponen
    disponibilidad de préstamo; no se modela margen, impacto o spread bid-ask.
    """
    px = np.asarray(prices, dtype=float)
    betas = np.asarray(beta, dtype=float)
    decisions = np.asarray(decisions)
    if px.ndim != 2 or px.shape[1] != 2 or betas.shape != px.shape or len(decisions) != len(px):
        raise ValueError('Dimensiones incompatibles: se requieren dos activos')
    if not np.all(np.isfinite(px)) or np.any(px <= 0):
        raise ValueError('Los precios deben ser positivos y finitos')
    if not (capital > 0 and 0 < gross_limit <= 1 and fee >= 0 and borrow >= 0 and 0 <= rebalance_band < 1):
        raise ValueError('Parámetros financieros no válidos')

    cash = float(capital)
    holdings = np.zeros(2, dtype=int)
    rows = []
    cost_total = 0.0

    for t, p in enumerate(px):
        before = holdings.copy()
        # El stock de posiciones se marca al cierre t; aún no se opera en t.
        borrow_cost = float(np.sum(np.maximum(-before, 0) * p) * borrow / 365.0) if t else 0.0
        cash -= borrow_cost
        equity_before_trade = float(cash + before @ p)

        desired = int(decisions[t - 1]) if t else 0
        if desired not in (-1, 0, 1):
            raise ValueError('Las decisiones deben ser -1, 0 o +1')
        b = betas[t - 1] if t else np.array([1., -1.])
        if not np.all(np.isfinite(b)) or equity_before_trade <= 0:
            desired = 0

        target = np.zeros(2, dtype=int)
        if desired:
            signed = desired * b
            relative_notional = np.abs(signed * p)
            if relative_notional.sum() > 0:
                allocation = equity_before_trade * gross_limit * relative_notional / relative_notional.sum()
                target = np.sign(signed).astype(int) * np.floor(allocation / p).astype(int)

        # Banda de no-rebalanceo: no se modifica una posicion si ambos activos
        # conservan la misma direccion y el ajuste bruto requerido es pequeno.
        # Las entradas, salidas y cambios de direccion siempre se ejecutan.
        # El umbral se expresa como fraccion de la exposicion bruta objetivo.
        skipped_rebalance = False
        if rebalance_band > 0 and desired and np.any(before) and np.any(target):
            same_directions = np.array_equal(np.sign(before), np.sign(target))
            target_turnover = float(np.sum(np.abs(target - before) * p))
            reference = max(float(equity_before_trade * gross_limit), 1e-12)
            retained_gross = float(np.sum(np.abs(before * p)))
            # Si mantener los titulos incumple el limite, SIEMPRE se rebalancea.
            retain_allowed = retained_gross <= max(equity_before_trade, 0) * gross_limit + 1e-8
            if same_directions and retain_allowed and target_turnover / reference < rebalance_band:
                target = before.copy()
                skipped_rebalance = True

        # Una posición dimensionada con patrimonio previo a comisiones puede
        # violar el límite después de pagar. Reducimos acciones enteras hasta
        # satisfacer el límite con el patrimonio POST costos.
        while True:
            delta = target - before
            commission = float(np.sum(np.abs(delta) * p) * fee)
            equity_after_trade = equity_before_trade - commission
            gross = float(np.sum(np.abs(target) * p))
            if gross <= max(equity_after_trade, 0.0) * gross_limit + 1e-8:
                break
            if not np.any(target):
                # Patrimonio insuficiente incluso después de liquidar.
                break
            idx = int(np.argmax(np.abs(target) * p))
            target[idx] -= int(np.sign(target[idx]))

        delta = target - before
        commission = float(np.sum(np.abs(delta) * p) * fee)
        cash -= float(delta @ p) + commission
        holdings = target
        equity = float(cash + holdings @ p)
        gross = float(np.sum(np.abs(holdings * p)))
        breach = bool(gross > max(equity, 0.0) * gross_limit + 1e-8)
        if breach:
            raise RuntimeError('Exposición bruta excede el máximo después de costos')

        traded = bool(np.any(delta))
        if not traded:
            event = 'sin_operacion'
        elif not np.any(before) and np.any(target):
            event = 'entrada'
        elif np.any(before) and not np.any(target):
            event = 'salida'
        elif np.any(before) and np.any(target) and np.any(
            np.sign(before[before != 0]) != np.sign(target[before != 0])):
            event = 'cambio_direccion'
        else:
            event = 'rebalanceo'

        cost_total += commission + borrow_cost
        rows.append({
            'cash': float(cash), 'shares_a': int(holdings[0]), 'shares_b': int(holdings[1]),
            'position': int(desired), 'trade_notional': float(np.sum(np.abs(delta) * p)),
            'commission': commission, 'borrow': borrow_cost, 'cumulative_cost': cost_total,
            'gross_exposure': gross, 'equity': equity,
            'accounting_error': float(equity - (cash + holdings @ p)),
            'trade_event': event,
            'commission_entry_exit': commission if event in ('entrada', 'salida', 'cambio_direccion') else 0.,
            'commission_rebalance': commission if event == 'rebalanceo' else 0.,
            'gross_limit_breached': breach,
            'rebalance_skipped': skipped_rebalance,
        })

    result = pd.DataFrame(rows, index=prices.index if hasattr(prices, 'index') else None)
    result['return'] = result.equity.pct_change().fillna(0.)
    result['drawdown'] = result.equity / result.equity.cummax() - 1.
    return result
