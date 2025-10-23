'''
This module contains BaseFitter
'''
from typing                   import cast
import textwrap

from omegaconf                import OmegaConf, DictConfig
from dmu.stats.fitter         import Fitter
from dmu.generic              import utilities  as gut
from dmu.stats                import utilities  as sut
from dmu.logging.log_store    import LogStore
from zfit.result              import FitResult  as zres
from zfit.data                import Data       as zdata
from zfit.pdf                 import BasePDF    as zpdf

log=LogStore.add_logger('fitter:base_fitter')
# ------------------------
class BaseFitter:
    '''
    Fitting base class, meant to

    - Provide basic functionality to fiters for data and simulation
    - Behave as a dependency sink, avoiding circular imports
    '''
    # ------------------------
    def __init__(self):
        '''
        Used to hold attributes passed from derived classes
        '''
        self._sample  : str = ''
        self._trigger : str = ''
        self._project : str = ''
        self._q2bin   : str = ''
        self._sig_yld : str = 'yld_signal' # Used to locate signal yield in order to calculate sensitivity
    # ------------------------
    def _fit(
        self,
        cfg   : DictConfig,
        data  : zdata,
        model : zpdf,
        d_cns : dict[str,tuple[float,float]]|None = None) -> zres:
        '''
        Parameters
        --------------------
        cfg  : Fitting configuration
        data : Zfit data object
        model: Zfit PDF
        d_cns: Dictionary mapping parameter names to tuples of value and error
               This is needed to apply constraints to fit

        Returns
        --------------------
        DictConfig object with parameters names, values and errors
        '''
        fit_cfg = OmegaConf.to_container(cfg, resolve=True)
        fit_cfg = cast(dict, fit_cfg)

        if d_cns is not None:
            fit_cfg['constraints'] = d_cns

        ftr = Fitter(pdf=model, data=data)
        res = ftr.fit(cfg=fit_cfg)

        return res
    # ------------------------
    def _get_sensitivity(self, res : zres|None) -> float:
        '''
        Parameters
        --------------
        res: Result object from fit

        Returns
        --------------
        fit sensitivity in %
        '''
        if res is None:
            log.debug('Missing result object, cannot get sensitivity')
            return -1

        cres = sut.zres_to_cres(res=res)

        if self._sig_yld not in cres:
            log.info('Missing nsig entry, cannot get sensitivity')
            return -1

        value = cres[self._sig_yld]['value']
        error = cres[self._sig_yld]['error']

        return 100 * error / value
    # --------------------------
    def _brem_cuts_from_cuts(self, cuts : dict[str,str]) -> str:
        '''
        Parameters
        --------------
        cuts: Dictionary with cuts used for fit

        Returns
        --------------
        String with brem requirements
        '''
        l_brem_cut = []
        for cut in cuts.values():
            if 'nbrem' not in cut:
                continue
            l_brem_cut.append(cut)

        brem_cuts = '; '.join(l_brem_cut)

        return brem_cuts
    # --------------------------
    def _get_selection_text(self, selection : DictConfig) -> tuple[str,str]:
        '''
        Parameters
        --------------
        selection: Object holding fitting and default selection
                   It should contain the fit and default selections in
                   the `fit` and `default` keys

        Returns
        --------------
        Tuple with:

        - Multiple lines with cuts that were used for fit, but are not default, plus MVA cut
        - Brem categories choice
        '''
        # For components like combinatorial, there is no MC sample
        # Therefore the selection or brem category does not make sense
        if self._sample == 'NA':
            return '', ''

        cuts_def  = selection.default
        cuts_fit  = selection.fit
        brem_cuts = self._brem_cuts_from_cuts(cuts=cuts_fit)

        l_expr = []
        # Collect all the cuts that are different
        # from default selection
        for name, fit_expr in cuts_fit.items():
            if name not in cuts_def:
                l_expr.append(fit_expr)
                continue

            def_expr = cuts_def[name]
            if fit_expr != def_expr:
                l_expr.append(fit_expr)

        # Remove differences in brem, will be done separately
        l_expr_no_brem = [ expr for expr in l_expr if 'nbrem' not in expr ]
        new_cuts       = '\n'.join(l_expr_no_brem)

        return new_cuts, brem_cuts
    # --------------------------
    def _entries_from_data(self, data : zdata) -> int:
        '''
        Parameters
        ---------------
        data: Dataset used in the fit

        Returns
        ---------------
        Number of entries in data that were used for the fit,
        which are in the fit observable range
        '''
        obs          = data.space
        [minx, maxx] = sut.range_from_obs(obs=obs)

        arr_mass = data.to_numpy()
        mask     = (minx < arr_mass) & (arr_mass < maxx)
        arr_mass = arr_mass[mask]
        nentries = len(arr_mass)

        return nentries
    # --------------------------
    def _get_text(
        self,
        data      : zdata,
        res       : zres|None,
        selection : DictConfig) -> tuple[str,str]:
        '''
        Parameters
        --------------
        data: Zfit data used for fit
        res : zfit result object
        Selection: Object storing selections for `fit` and `default` keys

        Returns
        --------------
        Tuple with:

        - Title for fit plot
        - Text that goes inside plot with selection information
        '''
        nentries          = self._entries_from_data(data=data)
        sel_txt, brem_txt = self._get_selection_text(selection=selection)

        sensitivity = self._get_sensitivity(res=res)
        title       = f'$\\delta={sensitivity:.2f}$%; Entries={nentries:.0f}; Brem:{brem_txt}'

        return title, sel_txt
    # ------------------------
    def _save_fit(
        self,
        cut_cfg  : DictConfig,
        plt_cfg  : DictConfig,
        out_path : str,
        model    : zpdf|None,
        res      : zres|None,
        data     : zdata,
        d_cns    : dict[str,tuple[float,float]]|None=None) -> None:
        '''
        Parameters
        --------------
        cut_cfg  : Selection used for fit in DictConfig object
                   Should contain keys `default` and `fit` the values
                   are the selection.
        plt_cfg  : Plotting configuration
        out_path : Directory where fit will be saved
        model    : PDF from fit, can be None if dataset was empty
        res      : Zfit result object, can be None if fit was to get a KDE
        data     : data from fit
        d_cns    : Dictionary mapping parameter name to value error tuple.
                   Used for constraining that parameter
        '''
        # If no entries were present
        # There will not be PDF
        title, text         = self._get_text(data=data, res=res, selection=cut_cfg)
        text                = '\n'.join(textwrap.wrap(text, width=40))
        plt_cfg['title'   ] = title
        plt_cfg['ext_text'] = text

        sel_path = f'{out_path}/selection.yaml'
        gut.dump_json(cut_cfg, sel_path, exists_ok=True)

        sut.save_fit(
            data   = data,
            model  = model,
            res    = res,
            d_const= d_cns,
            plt_cfg= plt_cfg,
            fit_dir= out_path)
# ------------------------
