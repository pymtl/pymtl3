#=========================================================================
# BehavioralRTLIRGenL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L3 behavioral RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

import pymtl
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.errors import PyMTLSyntaxError

from .BehavioralRTLIRGenL2Pass import BehavioralRTLIRGeneratorL2


class BehavioralRTLIRGenL3Pass( BasePass ):
  def __call__( s, m ):
    """ generate RTLIR for all upblks of m """
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()
    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL3( m )

    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = \
          visitor.enter( blk, m.get_update_block_ast( blk ) )

class BehavioralRTLIRGeneratorL3( BehavioralRTLIRGeneratorL2 ):
  def __init__( s, component ):
    super( BehavioralRTLIRGeneratorL3, s ).__init__( component )

  def visit_Call( s, node ):
    """Return behavioral RTLIR of a method call.
    
    At L3 we need to support the syntax of struct instantiation in upblks.
    This is achieved by function calls like `struct( 1, 2, 0 )`.
    """
    obj = s.get_call_obj( node )
    if isinstance(obj, type) and not issubclass(obj, pymtl.Bits) and obj is not bool:
      if node.args:
        raise PyMTLSyntaxError(
          s.blk, node, 'only keyword args are accepted by struct instantiation!'
        )
      keywords = []
      kwargs = []
      for keyword in node.keywords:
        keywords.append( keyword.arg )
        kwargs.append( s.visit( keyword.value ) )
      ret = StructInst( obj, keywords, kwargs )
      ret.ast = node
      return ret

    else:
      return super( BehavioralRTLIRGeneratorL3, s ).visit_Call( node )
