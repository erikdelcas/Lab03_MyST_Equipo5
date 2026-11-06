import numpy as np
import pandas as pd
from cointegration.screen import rolling_johansen


def _prices(n=190):
    rng = np.random.default_rng(42)
    x = 90 + np.cumsum(rng.normal(0, .7, n))
    y = x + rng.normal(0, .5, n)
    return pd.DataFrame({'a': x, 'b': y}, index=pd.date_range('2020-01-01', periods=n, freq='B'))


def test_rolling_no_uses_future():
    p = _prices()
    a = rolling_johansen(p.iloc[:160], window=80, step=10)
    b = rolling_johansen(p, window=80, step=10)
    assert a.index.equals(b.loc[a.index].index)
    np.testing.assert_allclose(a['beta_b'].values, b.loc[a.index, 'beta_b'].values, equal_nan=True)


def test_rolling_normalization_and_window_timing():
    out = rolling_johansen(_prices(), window=80, step=10)
    assert len(out) == 12
    assert out.index[0] == _prices().index[79]
    assert np.allclose(out.loc[out.beta_a.notna(), 'beta_a'], 1.0)


def test_rolling_rejects_bad_shape():
    import pytest
    with pytest.raises(ValueError):
        rolling_johansen(np.ones((100, 3)), window=40)
