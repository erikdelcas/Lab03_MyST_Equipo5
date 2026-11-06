import numpy as np
import pandas as pd
from backtest.engine import simulate


def sample():
    idx=pd.date_range('2021-01-01', periods=12)
    px=pd.DataFrame({'a':[100,100,101,100,100,99,99,100,101,100,100,100],
                     'b':[100,100,100,101,100,100,101,100,100,100,101,100]}, index=idx)
    beta=np.array([[1.,-1.]]*len(px))
    d=np.array([0,1,1,1,1,1,1,1,0,0,0,0])
    return px,beta,d


def test_zero_band_backward_compatible():
    args=sample()
    a=simulate(*args)
    b=simulate(*args,rebalance_band=0)
    for col in ['equity','commission','gross_exposure','shares_a','shares_b']:
        np.testing.assert_allclose(a[col],b[col])


def test_large_band_reduces_same_direction_rebalances_but_not_exit():
    px,beta,d=sample()
    daily=simulate(px,beta,d,fee=0.00125)
    band=simulate(px,beta,d,fee=0.00125,rebalance_band=.50)
    assert band['commission_rebalance'].sum() <= daily['commission_rebalance'].sum()+1e-9
    assert band['rebalance_skipped'].any()
    assert band['shares_a'].iloc[-1] == 0 and band['shares_b'].iloc[-1] == 0


def test_gross_limit_and_accounting():
    px,beta,d=sample()
    bt=simulate(px,beta,d,rebalance_band=.05)
    assert (bt['gross_exposure'] <= .8*bt['equity']+1e-6).all()
    assert (bt['accounting_error'].abs()<1e-7).all()


def test_no_signal_change_from_band():
    px,beta,d=sample()
    a=simulate(px,beta,d,rebalance_band=0)
    b=simulate(px,beta,d,rebalance_band=.2)
    assert np.array_equal(a['position'],b['position'])
