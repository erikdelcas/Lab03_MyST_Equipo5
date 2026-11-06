import numpy as np
import pandas as pd
from performance.trade_ledger import build_trade_ledger


def make_case(pos,px,fee=0.00125):
    px=np.array(px,float)
    holdings=np.array(pos,int)
    cash=10000.; rows=[]
    for t,(h,p) in enumerate(zip(holdings,px)):
        before=holdings[t-1] if t else np.array([0,0])
        delta=h-before
        charge=float(np.sum(np.abs(delta)*p)*fee)
        cash-=float(delta@p)+charge
        rows.append(dict(shares_a=h[0],shares_b=h[1],price_a=p[0],price_b=p[1],commission=charge,borrow=0.,equity=cash+h@p,partition='test'))
    return pd.DataFrame(rows,index=pd.date_range('2026-01-01',periods=len(rows)))


def test_flat_round_trip_reconciles():
    x=make_case([[2,-2],[2,-2],[0,0]],[[100,100],[105,98],[106,96]])
    d=build_trade_ledger(x)
    assert len(d)==1 and d.iloc[0].status=='cerrada'
    assert np.isclose(d.net_pnl.sum(),x.equity.iloc[-1]-(x.equity.iloc[0]+x.commission.iloc[0]))
    assert d.iloc[0].holding_days==2


def test_rebalance_is_same_episode():
    x=make_case([[2,-2],[3,-3],[0,0]],[[100,100],[101,99],[102,98]])
    d=build_trade_ledger(x)
    assert len(d)==1 and d.iloc[0].rebalance_days==1
    assert np.isclose(d.net_pnl.sum(),x.equity.iloc[-1]-(x.equity.iloc[0]+x.commission.iloc[0]))


def test_reversal_creates_two_episodes():
    x=make_case([[2,-2],[-2,2],[0,0]],[[100,100],[101,99],[103,97]])
    d=build_trade_ledger(x)
    assert len(d)==2 and set(d.direction)=={'spread_largo','spread_corto'}
    assert np.isclose(d.net_pnl.sum(),x.equity.iloc[-1]-(x.equity.iloc[0]+x.commission.iloc[0]))


def test_open_trade_not_fictitiously_liquidated():
    x=make_case([[2,-2],[2,-2]],[[100,100],[102,99]])
    d=build_trade_ledger(x)
    assert len(d)==1 and d.iloc[0].status=='abierta' and pd.isna(d.iloc[0].exit_date)
    assert np.isclose(d.net_pnl.sum(),x.equity.iloc[-1]-(x.equity.iloc[0]+x.commission.iloc[0]))
