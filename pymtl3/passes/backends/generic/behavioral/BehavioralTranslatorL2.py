#=========================================================================
# BehavioralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L2 behavioral translator."""

from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL2Pass import (
    BehavioralRTLIRGenL2Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL2Pass import (
    BehavioralRTLIRTypeCheckL2Pass,
)

from .BehavioralTranslatorL1 import BehavioralTranslatorL1


class BehavioralTranslatorL2( BehavioralTranslatorL1 ):

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_behavioral_trans_metadata( s, tr_top ):
    s.behavioral.tmpvars = {}
    s.behavioral.decl_tmpvars = {}
    super().gen_behavioral_trans_metadata( tr_top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL2Pass( s.tr_top ) )
    m.apply( BehavioralRTLIRTypeCheckL2Pass( s.tr_top ) )
    s.behavioral.rtlir[m] = \
        m.get_metadata( BehavioralRTLIRGenL2Pass.rtlir_upblks )
    s.behavioral.freevars[m] = \
        m.get_metadata( BehavioralRTLIRTypeCheckL2Pass.rtlir_freevars )
    s.behavioral.tmpvars[m] = \
        m.get_metadata( BehavioralRTLIRTypeCheckL2Pass.rtlir_tmpvars )

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  # Override
  def translate_behavioral( s, m ):
    """Translate behavioral part of `m`.

    Support for translating temporary variables is added at level 2.
    """
    super().translate_behavioral(m)

    # Generate temporary variable declarations
    tmpvars = []
    for (id_, upblk_id), rtype in s.behavioral.tmpvars[m].items():
      assert isinstance(rtype, rt.Wire), \
        f"temporary variable {id_} in upblk {upblk_id} is not a signal!"
      dtype = rtype.get_dtype()
      tmpvars.append( s.rtlir_tr_behavioral_tmpvar(
        id_,
        upblk_id,
        s.rtlir_data_type_translation( m, dtype )
      ) )
    s.behavioral.decl_tmpvars[m] = s.rtlir_tr_behavioral_tmpvars( tmpvars )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  def rtlir_tr_behavioral_tmpvars( s, tmpvars ):
    raise NotImplementedError()

  def rtlir_tr_behavioral_tmpvar( s, name, upblk_name, dtype ):
    raise NotImplementedError()
