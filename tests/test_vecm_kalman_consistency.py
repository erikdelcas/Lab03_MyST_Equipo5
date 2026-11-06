import numpy as np
from kalman.filters import signal_filter, hedge_filter
from strategy.vecm_signals import vecm_innovations_dynamic


def _prices(n=280, seed=42):
    rng=np.random.default_rng(seed)
    b=30+np.cumsum(rng.normal(0, 0.1, n))
    a=b+0.5*rng.standard_normal(n)
    return np.column_stack([a,b])


def test_dynamic_projection_identical_to_fixed_when_beta_constant():
    p=_prices()
    # Hay que usar el beta ajustado por el propio VECM para esta identidad.
    from statsmodels.tsa.vector_ar.vecm import VECM
    fit=VECM(p[:170],k_ar_diff=2,coint_rank=1,deterministic='n').fit()
    beta=fit.beta[:,0]/fit.beta[0,0]
    weights=np.tile(beta,(len(p),1))
    dyn, fixed, _, _=vecm_innovations_dynamic(p,170,weights)
    np.testing.assert_allclose(dyn[3:],fixed[3:],rtol=1e-10,atol=1e-10)


def test_projection_uses_previous_beta_not_current():
    p=_prices()
    w=np.tile([1.,-1.],(len(p),1))
    w[201]=[1.,-10.]
    a,_,_,_=vecm_innovations_dynamic(p,170,w)
    altered=w.copy(); altered[201]=[1.,-100.]
    b,_,_,_=vecm_innovations_dynamic(p,170,altered)
    assert a[201]==b[201]
    assert not np.isclose(a[202],b[202])


def test_no_future_values_affect_fixed_prior_filter():
    values=np.r_[np.full(15,np.nan),np.sin(np.arange(200)/7)]
    a=signal_filter(values)['z'][100]
    b=signal_filter(values[:101])['z'][100]
    np.testing.assert_allclose(a,b,rtol=0,atol=1e-12)


def test_kalman_hedge_sign_convention():
    p=_prices()
    out=hedge_filter(p)
    assert np.all(out['beta'][:,0]==1.0)
