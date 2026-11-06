import numpy as np
from kalman.filters import signal_filter


def test_both_states_and_gains_available():
    x=np.random.default_rng(42).normal(size=220)
    out=signal_filter(x)
    for key in ('predictive_mean','predictive_variance','predictive_sigma',
                'variance_gain','posterior_log_variance','variance_state_uncertainty'):
        assert out[key].shape==(len(x),)
        assert np.isfinite(out[key]).all()
    assert (out['predictive_variance']>0).all()
    assert ((out['variance_gain']>=0)&(out['variance_gain']<1)).all()


def test_no_lookahead_including_nan_prefix():
    x=np.r_[np.full(10,np.nan),np.sin(np.arange(210)/8.)]
    a=signal_filter(x)
    for t in (40,80,160):
        b=signal_filter(x[:t+1])
        for key in ('z','predictive_mean','predictive_sigma','variance_gain'):
            np.testing.assert_allclose(a[key][t],b[key][t],atol=1e-12,rtol=0)


def test_variance_adapts_to_change_in_scale():
    rng=np.random.default_rng(8)
    x=np.r_[rng.normal(0,.5,250),rng.normal(0,4,300)]
    out=signal_filter(x)
    assert np.median(out['predictive_variance'][450:]) > np.median(out['predictive_variance'][100:240])


def test_missing_values_do_not_generate_signals():
    x=np.r_[np.full(40,np.nan),np.ones(10)]
    out=signal_filter(x)
    assert np.isnan(out['z'][:40]).all()
    assert np.isfinite(out['z'][40:]).all()
