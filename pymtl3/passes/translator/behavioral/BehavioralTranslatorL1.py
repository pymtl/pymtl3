#=========================================================================
# BehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L1 behavioral translator."""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL1Pass import (
    BehavioralRTLIRGenL1Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL1Pass import (
    BehavioralRTLIRTypeCheckL1Pass,
)

from .BehavioralTranslatorL0 import BehavioralTranslatorL0


class BehavioralTranslatorL1( BehavioralTranslatorL0 ):
  def __init__( s, top ):
    super( BehavioralTranslatorL1, s ).__init__( top )
    s.gen_behavioral_trans_metadata( top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  def gen_behavioral_trans_metadata( s, top ):
    s.behavioral.rtlir = {}
    s.behavioral.freevars = {}
    s.behavioral.upblk_srcs = {}
    s.behavioral.decl_freevars = {}
    s._gen_behavioral_trans_metadata( top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL1Pass() )
    m.apply( BehavioralRTLIRTypeCheckL1Pass() )
    s.behavioral.rtlir[m] = \
        m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] = \
        m._pass_behavioral_rtlir_type_check.rtlir_freevars

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  # Override
  def translate_behavioral( s, m ):
    """Translate behavioral part of `m`."""
    # Translate upblks
    upblk_srcs = []
    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }
    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        upblk_srcs.append( s.rtlir_tr_upblk_decl(
          blk, s.behavioral.rtlir[ m ][ blk ]
        ) )
    s.behavioral.upblk_srcs[m] = s.rtlir_tr_upblk_decls( upblk_srcs )

    # Generate free variable declarations
    freevars = []
    for name, fvar in s.behavioral.freevars[m].iteritems():
      rtype = rt.get_rtlir( fvar )
      if isinstance( rtype, rt.Array ):
        fvar_rtype = rtype.get_sub_type()
        array_rtype = rtype
      else:
        fvar_rtype = rtype
        array_rtype = None
      dtype = fvar_rtype.get_dtype()
      assert isinstance( dtype, rdt.Vector ), \
        '{} freevar should be an integer or a list of integers!'.format( name )
      freevars.append( s.rtlir_tr_behavioral_freevar(
        name,
        fvar_rtype,
        s.rtlir_tr_unpacked_array_type( array_rtype ),
        s.rtlir_tr_vector_dtype( dtype ),
        fvar
      ) )
    s.behavioral.decl_freevars[m] = s.rtlir_tr_behavioral_freevars(freevars)

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    raise NotImplementedError()

  def rtlir_tr_upblk_decl( s, upblk, rtlir_upblk ):
    raise NotImplementedError()

  def rtlir_tr_behavioral_freevars( s, freevars ):
    raise NotImplementedError()

  def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
    raise NotImplementedError()
