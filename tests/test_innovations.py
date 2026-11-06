import numpy as np
from strategy.vecm_signals import positions_from_z

def test_decision_logic():
    z=np.array([np.nan,-2.1,-1.5,.1,2.2,4.1])
    assert positions_from_z(z).tolist()==[0,1,1,0,-1,0]
