import numpy as np

def evaluate(frame):
    rets=frame['return'].to_numpy(dtype=float)
    mean=rets.mean(); std=rets.std(ddof=1); neg=rets[rets<0]; dn=neg.std(ddof=1) if len(neg)>1 else float('nan')
    n=len(rets);years=max(n/252,1e-9)
    total=float(frame.equity.iloc[-1]/frame.equity.iloc[0]-1)
    cagr=(1+total)**(1/years)-1 if total>-1 else -1.
    dd=float(frame.drawdown.min());
    return {'total_return':total,'cagr':cagr,'sharpe':float(mean/std*np.sqrt(252)) if std>0 else np.nan,
    'sortino':float(mean/dn*np.sqrt(252)) if np.isfinite(dn) and dn>0 else np.nan,
    'calmar':float(cagr/abs(dd)) if dd<0 else np.nan,'max_drawdown':dd,
    'net_profit':float(frame.equity.iloc[-1]-frame.equity.iloc[0]),
    'commissions':float(frame.commission.sum()),'borrow_cost':float(frame.borrow.sum()),
    'trade_days':int((frame.trade_notional>0).sum()),'positive_days_pct':float((rets>0).mean())}
