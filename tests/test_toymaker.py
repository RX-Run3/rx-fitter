'''
This module tests the class ToyMaker
'''
import pytest

from fitter.toy_maker      import ToyMaker
from dmu.stats             import utilities as sut
from dmu.generic           import utilities as gut
from dmu.logging.log_store import LogStore
from dmu.stats.fitter      import Fitter

log=LogStore.add_logger('fitter:test_toymaker')
# ----------------------
@pytest.fixture(scope='session', autouse=True)
def initialize():
    '''
    This will run before any test
    '''
    LogStore.set_level('dmu:stats:gofcalculator', 30)
    LogStore.set_level('dmu:statistics:fitter'  , 20)
# ----------------------
def test_simple() -> None:
    '''
    Simplest test of ToyMaker

    Parameters 
    -------------
    none
    '''
    log.info('')
    nll   = sut.get_nll(kind='s+b')
    res, _= Fitter.minimize(nll=nll, cfg={})

    cfg   = gut.load_conf(package='fitter_data', fpath='tests/toys/toy_maker.yaml')

    mkr   = ToyMaker(nll=nll, res=res, cfg=cfg)
    df    = mkr.get_parameter_information()
    l_col = ['Parameter', 'Value', 'Error', 'Gen', 'Toy', 'GOF', 'Converged']

    assert df.columns.to_list() == l_col

    pars  = nll.get_params()
    assert len(df) == cfg.ntoys * len(pars) 
# ----------------------
