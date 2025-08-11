'''
Module meant to hold tests for the DataPreprocessor class
'''
import os
import pytest
import matplotlib.pyplot as plt
from dmu.stats.zfit           import zfit
from dmu.generic              import utilities as gut
from dmu.stats                import utilities as sut
from dmu.logging.log_store    import LogStore
from omegaconf                import OmegaConf
from rx_data.rdf_getter       import RDFGetter
from zfit.interface           import ZfitData  as zdata
from fitter.data_preprocessor import DataPreprocessor

log=LogStore.add_logger('fitter:test_data_preprocessor')
# -------------------------------------------------
class Data:
    '''
    Meant to hold shared attributes
    '''
    user    = os.environ['USER']
    out_dir = f'/tmp/{user}/tests/fitter/data_preprocessor'
    os.makedirs(out_dir, exist_ok=True)
# -------------------------------------------------
def _validate_data(data : zdata, name : str) -> None:
    '''
    Makes validation plots from zfit data
    '''
    plt_path = f'{Data.out_dir}/{name}.png'

    arr_data = data.numpy()
    rng      = sut.range_from_obs(obs=data.space)
    if data.weights is None:
        arr_wgt = None
    else:
        arr_wgt = data.weights.numpy()

    log.info(f'Saving to: {plt_path}')
    plt.hist(arr_data, histtype='step', bins=100, range=rng, weights=arr_wgt)
    plt.savefig(plt_path)
    plt.close()
# -------------------------------------------------
@pytest.mark.parametrize('sample', [
    'DATA_24_MagDown_24c2',
    'Bu_JpsiK_mm_eq_DPC'])
def test_muon_data(sample : str):
    '''
    Tests class with toys
    '''
    obs = zfit.Space('B_Mass', limits=(5180, 6000))
    name= f'{sample}_muon_data'

    with RDFGetter.max_entries(100_000):
        prp = DataPreprocessor(
            obs    = obs,
            out_dir= name,
            sample = sample,
            trigger= 'Hlt2RD_BuToKpMuMu_MVA',
            project= 'rx',
            wgt_cfg= None,
            q2bin  = 'jpsi')
        dat = prp.get_data()

    _validate_data(data=dat, name=name)
# -------------------------------------------------
@pytest.mark.parametrize('sample', [
    'DATA_24_MagDown_24c2',
    'Bu_JpsiK_ee_eq_DPC'])
@pytest.mark.parametrize('brem_cat', [0, 1, 2])
def test_brem_cat_data(sample : str, brem_cat : int):
    '''
    Tests class with toys
    '''
    obs = zfit.Space('B_Mass', limits=(4500, 6000))
    name= f'{sample}_brem_{brem_cat:03}'
    cut = {'brem' : f'nbrem == {brem_cat}'}

    with RDFGetter.max_entries(100_000):
        prp = DataPreprocessor(
            obs    = obs,
            out_dir= name,
            sample = sample,
            trigger= 'Hlt2RD_BuToKpEE_MVA',
            project= 'rx',
            cut    =  cut, 
            wgt_cfg= None,
            q2bin  = 'jpsi')
        dat = prp.get_data()

    _validate_data(data=dat, name=name)
# -------------------------------------------------
@pytest.mark.parametrize('sample', [
    'Bu_piplpimnKpl_eq_sqDalitz_DPC',
    'Bu_KplKplKmn_eq_sqDalitz_DPC'])
@pytest.mark.parametrize('region', ['kpipi' ,     'kkk'])
@pytest.mark.parametrize('kind'  , ['signal', 'control'])
def test_with_pid_weights(
    sample : str,
    region : str, 
    kind   : str) -> None:
    '''
    Parameters
    -------------
    sample: MC sample, weights are not applied to data
    region: Kind of control region
    kind  : Either 'signal' or 'control'
    '''
    cfg_spl = gut.load_conf(package='fitter_data', fpath='model/weights/splitting.yaml')
    cfg_wgt = gut.load_conf(package='fitter_data', fpath='model/weights/weights.yaml')

    wgt_cfg = {'PID' : {
           'splitting' : cfg_spl,
           'weights'   : cfg_wgt}}

    obs     = zfit.Space(f'B_Mass_{region}', limits=(4500, 6000))
    wgt_cfg = OmegaConf.create(wgt_cfg)
    cut     = {
        'brem' : 'nbrem == 1',
        'pid_l': '(1)'}

    name = f'with_pid_weights_{sample}_{region}_{kind}'
    with RDFGetter.max_entries(1000_000),\
         RDFGetter.default_excluded(names=[]):
        prp = DataPreprocessor(
            obs    = obs,
            out_dir= name,
            sample = sample,
            trigger= 'Hlt2RD_BuToKpEE_MVA_noPID',
            project= 'nopid',
            cut    = cut, 
            wgt_cfg= wgt_cfg,
            is_sig = kind == 'signal',
            q2bin  = 'jpsi')
        dat = prp.get_data()

    _validate_data(data=dat, name=name)
# -------------------------------------------------
