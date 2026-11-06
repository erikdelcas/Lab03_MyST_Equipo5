import numpy as np
import pandas as pd
from backtest.engine import simulate

def test_accounting_and_costs():
    p=pd.DataFrame({'A':[100.,101,102,99,98,100],'B':[50.,51,50,49,48,50]})
    beta=np.tile([1.,-1.],(len(p),1))
    bt=simulate(p,beta,np.array([1,1,0,-1,-1,0]))
    assert np.abs(bt.accounting_error).max()<1e-8
    assert np.allclose(bt.commission,bt.trade_notional*.00125)
    assert (bt.borrow>=0).all()
    assert bt.position.iloc[0]==0
    assert bt.position.iloc[1]==1

def test_no_same_close_lookahead():
    p=pd.DataFrame({'A':[100.,100,100,100],'B':[50.,50,50,50]})
    beta=np.tile([1.,-1.],(4,1))
    bt=simulate(p,beta,[0,1,0,0])
    assert bt.position.tolist()==[0,0,1,0]
