"""Lectura y comprobación de comparaciones walk-forward ya calculadas.

No hace selección de umbrales ni utiliza test/validación para entrenar.
"""
from pathlib import Path
import pandas as pd

REQUIRED = {'pair','policy','partition','entry_z','exit_z','return_net',
            'max_dd','sharpe','commission','borrow','trade_days'}
POLICY = {'baseline':'Original (2.0 / 0.5)', 'seleccion_train':'Calibrada en entrenamiento'}
PARTITIONS = ('test','validation')


def load_comparison(path, pair):
    path = Path(path)
    if not path.is_file():
        return None
    df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f'Columnas faltantes en walkforward_oos_comparison.csv: {sorted(missing)}')
    selected = df.loc[(df['pair'] == pair) & df['partition'].isin(PARTITIONS)
                      & df['policy'].isin(POLICY)].copy()
    for col in ('entry_z','exit_z','return_net','max_dd','sharpe','commission','borrow','trade_days'):
        selected[col] = pd.to_numeric(selected[col], errors='raise')
    selected['politica'] = selected['policy'].map(POLICY)
    selected['periodo'] = selected['partition'].map({'test':'Prueba','validation':'Validación'})
    selected['rendimiento_pct'] = 100 * selected['return_net']
    selected['drawdown_pct'] = 100 * selected['max_dd']
    if selected.duplicated(['policy','partition']).any():
        raise ValueError('Filas duplicadas para política y partición')
    return selected


def commission_savings(df):
    """Ahorro positivo significa menor comisión para la calibrada; por partición."""
    pivot = df.pivot(index='partition', columns='policy', values='commission')
    if not {'baseline','seleccion_train'}.issubset(pivot.columns):
        return pd.Series(dtype=float)
    return pivot['baseline'] - pivot['seleccion_train']
