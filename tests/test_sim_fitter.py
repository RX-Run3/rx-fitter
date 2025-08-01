'''
This module is meant to test the SimFitter class
'''
import pytest

from dmu.stats.zfit         import zfit
from dmu.generic            import utilities as gut
from dmu.workflow.cache     import Cache
from rx_data.rdf_getter     import RDFGetter
from rx_selection           import selection as sel

from fitter.sim_fitter  import SimFitter

# ---------------------------------------------------
def test_nomc():
    '''
    Test for components that have no MC associated
    '''
    obs = zfit.Space('B_Mass', limits=(4500, 7000))

    cfg = gut.load_conf(package='fitter_data', fpath='rare/electron/combinatorial.yaml')
    ftr = SimFitter(
        component= 'combinatorial',
        obs     = obs,
        cfg     = cfg,
        trigger = 'Hlt2RD_BuToKpEE_MVA',
        project = 'rx',
        q2bin   = 'low')
    pdf = ftr.get_model()
# ---------------------------------------------------
def test_toy():
    '''
    Simplest test of fitter with toy data
    '''
    obs = zfit.Space('B_Mass', limits=(4500, 7000))

    cfg = gut.load_conf(package='fitter_data', fpath='tests/signal_toy.yaml')
    ftr = SimFitter(
        component= 'gauss_toy',
        obs     = obs,
        cfg     = cfg,
        trigger = '',
        project = '',
        q2bin   = '')
    ftr.get_model()
# ---------------------------------------------------
def test_nocat():
    '''
    Test for components without categories, e.g. muon
    '''
    obs = zfit.Space('B_Mass', limits=(5000, 5800))

    cfg = gut.load_conf(package='fitter_data', fpath='tests/signal_muon.yaml')
    with RDFGetter.max_entries(value=10_000):
        ftr = SimFitter(
            component= 'signal_muon',
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpMuMu_MVA',
            project = 'rx',
            q2bin   = 'jpsi')
        pdf = ftr.get_model()
# ---------------------------------------------------
def test_with_cat():
    '''
    Test for components with brem categories
    '''
    obs = zfit.Space('B_Mass', limits=(4500, 7000))

    cfg = gut.load_conf(package='fitter_data', fpath='tests/signal_electron.yaml')
    with RDFGetter.max_entries(value=100_000):
        ftr = SimFitter(
            component= 'signal_electron',
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = 'jpsi')
        pdf = ftr.get_model()
# ---------------------------------------------------
@pytest.mark.parametrize('component', ['bdkstee', 'bukstee', 'bsphiee'])
def test_kde(component : str):
    '''
    Test fitting with KDE
    '''
    obs = zfit.Space('B_Mass', limits=(4500, 7000))

    cfg = gut.load_conf(package='fitter_data', fpath=f'tests/{component}.yaml')
    with RDFGetter.max_entries(value=100_000):
        ftr = SimFitter(
            component= component,
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = 'central')
        ftr.get_model()
# ---------------------------------------------------
def test_ccbar_reso():
    '''
    Tests retriveval of PDF associated to ccbar inclusive decays
    '''
    component = 'ccbar'
    obs       = zfit.Space('B_const_mass_M', limits=(4500, 6000))
    cfg       = gut.load_conf(package='fitter_data', fpath=f'reso/electron/{component}.yaml')

    with RDFGetter.max_entries(value=-1),\
        RDFGetter.multithreading(nthreads=6):
        ftr = SimFitter(
            component= component,
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = 'jpsi')
        ftr.get_model()
# ---------------------------------------------------
def test_ccbar_rare():
    '''
    Tests retriveval of PDF associated to ccbar inclusive decays
    for rare modes, i.e. without jpsi mass constraint
    '''
    component = 'ccbar'
    mass      = 'B_Mass'
    q2bin     = 'high'

    obs       = zfit.Space(mass, limits=(4500, 6000))
    cfg       = gut.load_conf(package='fitter_data', fpath=f'rare/electron/{component}.yaml')

    with Cache.turn_off_cache(val=['SimFitter']),\
        sel.custom_selection(d_sel={
            'nobr0' : 'nbrem != 0',
            'bdt'   : 'mva_cmb > 0.8 && mva_prc > 0.8'}):
        ftr = SimFitter(
            component= component,
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = q2bin)
        ftr.get_model()
# ---------------------------------------------------
def test_signal_reso():
    '''
    Tests retriveval of PDF associated to ccbar inclusive decays
    '''
    component = 'signal_electron'
    obs       = zfit.Space('B_const_mass_M', limits=(5000, 5600))
    cfg       = gut.load_conf(package='fitter_data', fpath=f'tests/{component}.yaml')

    with RDFGetter.max_entries(value=200_000),\
        Cache.turn_off_cache(val=None), \
        sel.custom_selection(d_sel={
            'mass'  : '(1)',
            'nbrem' : 'nbrem != 0'}):
        ftr = SimFitter(
            component= component,
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = 'jpsi')
        ftr.get_model()
# ---------------------------------------------------
@pytest.mark.parametrize('name', ['name_001', 'name_002'])
def test_name(name : str):
    '''
    Will run test and specify the name argument
    '''
    component = 'ccbar'
    obs       = zfit.Space('B_const_mass_M', limits=(4500, 6000))
    cfg       = gut.load_conf(package='fitter_data', fpath=f'reso/electron/{component}.yaml')

    with RDFGetter.max_entries(value=-1),\
        RDFGetter.multithreading(nthreads=6):
        ftr = SimFitter(
            name     = name,
            component= component,
            obs      = obs,
            cfg      = cfg,
            trigger  = 'Hlt2RD_BuToKpEE_MVA',
            project  = 'rx',
            q2bin    = 'jpsi')
        ftr.get_model()
# ---------------------------------------------------
@pytest.mark.parametrize('component', ['kpipi', 'kkk'])
def test_weights(component : str):
    '''
    Test fitting weighted MC sample
    '''
    obs = zfit.Space('B_Mass_smr', limits=(4500, 7000))

    cfg = gut.load_conf(package='fitter_data', fpath=f'misid/electron/{component}.yaml')
    with RDFGetter.max_entries(value=-1):
        ftr = SimFitter(
            component= component,
            obs     = obs,
            cfg     = cfg,
            trigger = 'Hlt2RD_BuToKpEE_MVA_noPID',
            project = 'nopid',
            q2bin   = 'central')
        ftr.get_model()
