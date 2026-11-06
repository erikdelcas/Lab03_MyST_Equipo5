"""Genera bitácoras usando los CSV ya calculados; no ejecuta backtests."""
from pathlib import Path
import pandas as pd
from performance.trade_ledger import build_trade_ledger

ROOT=Path(__file__).resolve().parent
ART=ROOT/'artifacts'
files=sorted(ART.glob('*_backtest.csv'))
if not files:
    raise SystemExit('Sin backtests en artifacts/. Ejecuta primero python main.py')
for source in files:
    bt=pd.read_csv(source,parse_dates=['date']).set_index('date')
    ledger=build_trade_ledger(bt)
    dest=ART/f'{source.name.removesuffix("_backtest.csv")}_operaciones.csv'
    ledger.to_csv(dest,index=False,date_format='%Y-%m-%d')
    nclosed=int((ledger.status=='cerrada').sum()) if not ledger.empty else 0
    print(f'{source.stem}: {len(ledger)} episodios, {nclosed} cerrados; guardado: {dest.name}')
print('Las bitácoras se han generado a partir de los backtests existentes.')
