import numpy as np
from kalman.filters import signal_filter,hedge_filter

def test_causality_three_cutoffs():
    x=np.sin(np.arange(250)/7.)+np.arange(250)*.001
    for t in (65,127,201):
        a=signal_filter(x)['z'][t]
        b=signal_filter(x[:t+1])['z'][t]
        assert np.isclose(a,b,atol=1e-11)

def test_beta_normalization():
    x=np.arange(100.)
    p=np.column_stack([15+x*.1,10+x*.07])
    beta=hedge_filter(p)['beta']
    assert np.all(beta[:,0]==1.)
    assert np.isfinite(beta).all()

def test_innovation_var_positive():
    rng=np.random.default_rng(42)
    f=signal_filter(rng.standard_normal(500))
    assert np.all(f['predictive_sigma']>0)
    assert np.isfinite(f['gain']).all()
