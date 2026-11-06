"""Precios ajustados diarios con caché local, sin cambios en datos originales."""
import pandas as pd
from config import ROOT, CFG

def get_prices(tickers, force=False):
    cache = ROOT / 'data' / 'precios_ajustados.csv'
    if cache.exists() and not force:
        frame = pd.read_csv(cache, index_col=0, parse_dates=True)
    else:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError('Instala requirements.txt para descargar datos') from exc
        raw = yf.download(list(tickers), start=CFG.start, end=CFG.end,
                          auto_adjust=True, progress=False, threads=False)
        if raw.empty:
            raise RuntimeError('Sin datos descargados. Verifica conexión y tickers.')
        if isinstance(raw.columns, pd.MultiIndex):
            frame = raw['Close'].copy()
        else:
            frame = raw[['Close']].rename(columns={'Close':list(tickers)[0]})
        frame = frame.dropna(how='all').sort_index()
        cache.parent.mkdir(exist_ok=True)
        frame.to_csv(cache)
    missing = set(tickers)-set(frame.columns)
    if missing:
        raise ValueError(f'Faltan tickers: {missing}')
    frame = frame[list(tickers)].dropna().sort_index()
    if len(frame) < 2000:
        raise ValueError(f'Muestra demasiado corta: {len(frame)} días')
    if (frame<=0).any().any():
        raise ValueError('Precios inválidos')
    return frame

def split_602020(frame):
    n=len(frame); i=int(n*.60); j=int(n*.80)
    return frame.iloc[:i].copy(), frame.iloc[i:j].copy(), frame.iloc[j:].copy()
