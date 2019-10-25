#=========================================================================
# StructuralRTLIRGenL1Pass.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019
"""Provide L1 structural RTLIR generation pass."""

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype.RTLIRType import get_rtlir

from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL1Pass( BasePass ):
  def __init__( s, inst_conns ):
    s.inst_conns = inst_conns

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
      msg = '' if not e.args is None else e.args[0]
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
        f"Internal error: {const_name} is not a member of {m}"
      const_instance = getattr(m, const_name)
      ns.consts.append( ( const_name, const_rtype, const_instance ) )

  def sort_connections( s, m ):
    m_conns_set   = s.inst_conns[m]
    ordered_conns = [ *m.get_connect_order() ]
    assert len(ordered_conns) == len(m_conns_set)

    for i, x in enumerate(ordered_conns):
      if x not in m_conns_set:
        x = (x[1], x[0])
        assert x in m_conns_set, "There is a connection missing from "\
                                 "connect_order. Please contact PyMTL developers!"
        ordered_conns[i] = x

    m._pass_structural_rtlir_gen.connections = \
      [ (gen_signal_expr(m, x[0]), gen_signal_expr(m, x[1])) for x in ordered_conns ]
