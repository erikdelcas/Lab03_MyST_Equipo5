import pytest
from calibrar_walkforward import GRID, inner_folds, select_by_inner_folds, _score_fold


def test_folds_only_in_train_and_chronological():
    f = inner_folds(1938)
    assert len(f) == 4
    assert f[-1][1] == 1938
    assert all(0 < a < b <= 1938 for a, b in f)
    assert all(f[i][1] == f[i + 1][0] for i in range(3))


def test_grid_consistent():
    assert len(GRID) == 6
    assert all(0 < exit_ < entry < 4 for entry, exit_ in GRID)


def test_score_penalizes_drawdown():
    assert _score_fold(.01, -.2) < _score_fold(.01, -.1)


def test_selection_never_uses_oos_fields():
    rows = []
    for en, ex in GRID:
        for fold in range(1, 5):
            rows.append(dict(entry_z=en, exit_z=ex, fold=fold,
                             objective=1 if (en, ex) == (2.5, .5) else 0,
                             entry_days=3, secret_oos_score=-999999))
    (en, ex, status), _ = select_by_inner_folds(rows)
    assert (en, ex, status) == (2.5, .5, 'seleccion_interna')


def test_fallback_when_no_trades():
    rows = []
    for en, ex in GRID:
        for fold in range(1, 5):
            rows.append(dict(entry_z=en, exit_z=ex, fold=fold,
                             objective=1, entry_days=0))
    (_, _, status), _ = select_by_inner_folds(rows)
    assert status == 'baseline_no_elegibles'
