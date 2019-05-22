#=========================================================================
# BehavioralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L2 behavioral translator."""
from __future__ import absolute_import, division, print_function

import pymtl.passes.rtlir.RTLIRType as rt
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRGenL2Pass import (
    BehavioralRTLIRGenL2Pass,
)
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL2Pass import (
    BehavioralRTLIRTypeCheckL2Pass,
)

from .BehavioralTranslatorL1 import BehavioralTranslatorL1


class BehavioralTranslatorL2( BehavioralTranslatorL1 ):
  def __init__( s, top ):
    super( BehavioralTranslatorL2, s ).__init__( top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_behavioral_trans_metadata( s, top ):
    s.behavioral.tmpvars = {}
    s.behavioral.decl_tmpvars = {}
    super( BehavioralTranslatorL2, s ).gen_behavioral_trans_metadata( top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL2Pass() )
    m.apply( BehavioralRTLIRTypeCheckL2Pass() )
    s.behavioral.rtlir[m] = m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] = \
        m._pass_behavioral_rtlir_type_check.rtlir_freevars
    s.behavioral.tmpvars[m] = \
        m._pass_behavioral_rtlir_type_check.rtlir_tmpvars

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  # Override
  def translate_behavioral( s, m ):
    """Translate behavioral part of `m`.
    
    Support for translating temporary variables is added at level 2.
    """
    super(BehavioralTranslatorL2, s).translate_behavioral(m)

    # Generate temporary variable declarations
    tmpvars = []
    for (id_, upblk_id), rtype in s.behavioral.tmpvars[m].iteritems():
      assert isinstance(rtype, rt.Wire), \
        "temporary variable {} in upblk {} is not a signal!".format(id_, upblk_id)
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

  def rtlir_tr_tmpvars( s, tmpvars ):
    raise NotImplementedError()

  def rtlir_tr_tmpvar( s, name, upblk_name, dtype ):
    raise NotImplementedError()