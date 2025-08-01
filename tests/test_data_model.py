'''
This module has tests for the DataModel class
'''
from rx_selection          import selection as sel
from dmu.stats.zfit        import zfit
from dmu.generic           import utilities as gut
from dmu.stats             import utilities as sut
from dmu.logging.log_store import LogStore
from fitter.data_model     import DataModel

log=LogStore.add_logger('fitter:test_data_model')
# --------------------------
def test_resonant():
    '''
    Simplest test
    '''

    obs = zfit.Space('B_const_mass_M', limits=(5000, 6000))
    cfg = gut.load_conf(
        package='fitter_data',
        fpath  ='reso/electron/data.yaml')

    with sel.custom_selection(d_sel = {
        'mass' : '(1)',
        'block': 'block == 1 || block == 2'}):
        dmd = DataModel(
            cfg     = cfg,
            obs     = obs,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = 'jpsi',
            name    = 'simple')
        pdf = dmd.get_model()

    sut.print_pdf(pdf)
# --------------------------
def test_rare():
    '''
    Simplest test for rare mode
    '''
    q2bin = 'central'

    obs = zfit.Space('B_Mass_smr', limits=(4500, 7000))
    cfg = gut.load_conf(
        package='fitter_data',
        fpath  ='rare/electron/data.yaml')

    with sel.custom_selection(d_sel = {'mass' : '(1)', 'brmp' : 'nbrem != 0'}):
        dmd = DataModel(
            cfg     = cfg,
            obs     = obs,
            trigger = 'Hlt2RD_BuToKpEE_MVA',
            project = 'rx',
            q2bin   = q2bin)
        pdf = dmd.get_model()

    sut.print_pdf(pdf)
# --------------------------
def test_misid_rare():
    '''
    Test getting model for misid control region
    '''
    q2bin = 'central'

    obs = zfit.Space('B_Mass_smr', limits=(4500, 7000))
    cfg = gut.load_conf(
        package='fitter_data',
        fpath  ='misid/electron/data.yaml')

    l1_in_cr = '(L1_PROBNN_E < 0.2) || (L1_PID_E < 3.0)'
    l2_in_cr = '(L2_PROBNN_E < 0.2) || (L2_PID_E < 3.0)'

    with sel.custom_selection(d_sel = {
        'nobr0' : 'nbrem != 0',
        'pid_l' : f'({l1_in_cr}) || ({l2_in_cr})',
        'bdt'   : 'mva_cmb > 0.80 && mva_prc > 0.60'}):
        dmd = DataModel(
            cfg     = cfg,
            obs     = obs,
            trigger = 'Hlt2RD_BuToKpEE_MVA_noPID',
            project = 'nopid',
            q2bin   = q2bin)
        pdf = dmd.get_model()

    sut.print_pdf(pdf)
# --------------------------
