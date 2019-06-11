#=========================================================================
# StructuralRTLIRGenL1Pass.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019
"""Provide L1 structural RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype.RTLIRType import get_rtlir

from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL1Pass( BasePass ):
  def __init__( s, conns_self_self, conns_self_child, conns_child_child ):
    # connections_self_self, connections_self_child, connections_child_child
    s.c_ss = conns_self_self
    s.c_sc = conns_self_child
    s.c_cc = conns_child_child

  def __call__( s, tr_top ):
    """ generate structural RTLIR for component `tr_top` """
    if not hasattr( tr_top, '_pass_structural_rtlir_gen' ):
      tr_top._pass_structural_rtlir_gen = PassMetadata()
    s.tr_top = tr_top
    try:
      s.gen_rtlir_types( tr_top )
      s.gen_constants( tr_top )
      s.sort_connections( tr_top )
    except AssertionError as e:
      msg = '' if e.args[0] is None else e.args[0]
      raise RTLIRConversionError( tr_top, msg )

  def gen_rtlir_types( s, tr_top ):
    tr_top._pass_structural_rtlir_gen.rtlir_type = get_rtlir( tr_top )

  def gen_constants( s, m ):
    ns = m._pass_structural_rtlir_gen
    ns.consts = []
    rtype = ns.rtlir_type
    const_types = rtype.get_consts_packed()
    for const_name, const_rtype in const_types:
      assert hasattr(m, const_name), \
        "Internal error: {} is not a member of {}".format( const_name, m )
      const_instance = getattr(m, const_name)
      ns.consts.append( ( const_name, const_rtype, const_instance ) )

  def collect_connections( s, m ):
    return map( lambda x: \
      ((gen_signal_expr(m, x[0]), gen_signal_expr(m, x[1])), False), s.c_ss[m] )

  def sort_connections( s, m ):
    m_connections = s.collect_connections( m )
    connections = []
    for u, v in m.get_connect_order():
      _u, _v = gen_signal_expr( m, u ), gen_signal_expr( m, v )
      for idx, ( ( wr, rd ), visited ) in enumerate( m_connections ):

        if not visited and ( ( s.contains( _u, wr ) and s.contains( _v, rd ) ) or \
           ( s.contains( _u, rd ) and s.contains( _v, wr ) ) ):
          connections.append( ( wr, rd ) )
          m_connections[idx] = ( m_connections[idx][0], True )
    connections += map(lambda x:x[0],filter(lambda x:not x[1],m_connections))
    m._pass_structural_rtlir_gen.connections = connections

  def contains( s, obj, signal ):
    """Return if obj contains signal.

    At level 1 all signals have their corresponding object in `s.connect`.
    Therefore just checking whether obj is equal to signal is enough at level 1.
    """
    return obj == signal
