import pandas as pd
import pytest
from performance.walkforward_dashboard import load_comparison, commission_savings


def test_load_only_requested_pair_and_oos(tmp_path):
    data = pd.DataFrame([
        dict(pair='A',policy='baseline',partition='test',entry_z=2,exit_z=.5,return_net=-.05,max_dd=-.08,sharpe=-2,commission=100,borrow=2,trade_days=3),
        dict(pair='A',policy='seleccion_train',partition='test',entry_z=2.5,exit_z=.25,return_net=-.02,max_dd=-.03,sharpe=-1,commission=60,borrow=2,trade_days=2),
        dict(pair='B',policy='baseline',partition='test',entry_z=2,exit_z=.5,return_net=.1,max_dd=-.01,sharpe=2,commission=0,borrow=0,trade_days=0),
    ])
    p = tmp_path/'wf.csv'
    data.to_csv(p,index=False)
    res = load_comparison(p,'A')
    assert len(res)==2
    assert set(res['politica'])=={'Original (2.0 / 0.5)','Calibrada en entrenamiento'}
    assert res.loc[res.policy=='baseline','rendimiento_pct'].iloc[0] == pytest.approx(-5)
    assert commission_savings(res).loc['test']==pytest.approx(40)


def test_missing_file_is_graceful(tmp_path):
    assert load_comparison(tmp_path/'missing.csv','A') is None


def test_duplicate_policy_partition_rejected(tmp_path):
    row=dict(pair='A',policy='baseline',partition='test',entry_z=2,exit_z=.5,return_net=-.01,max_dd=-.02,sharpe=-1,commission=3,borrow=0,trade_days=2)
    p=tmp_path/'wf.csv'
    pd.DataFrame([row,row]).to_csv(p,index=False)
    with pytest.raises(ValueError,match='duplicadas'):
        load_comparison(p,'A')
