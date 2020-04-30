#=========================================================================
# StructuralRTLIRGenL1Pass.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019
"""Provide L1 structural RTLIR generation pass."""

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.PlaceholderConfigs import PlaceholderConfigs
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype.RTLIRType import RTLIRGetter

from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL1Pass( BasePass ):
  def __init__( s, inst_conns ):
    s.inst_conns = inst_conns

  def __call__( s, tr_top ):
    """ generate structural RTLIR for component `tr_top` """
    s.tr_top = tr_top
    if not hasattr( tr_top, "_rtlir_getter" ):
      tr_top._rtlir_getter = RTLIRGetter(cache=True)

    try:
      s._gen_metadata( tr_top )
    except AssertionError as e:
      msg = '' if not e.args is None else e.args[0]
      raise RTLIRConversionError( tr_top, msg )

  def _gen_metadata( s, m ):

    # Create namespace
    if not hasattr( m, '_pass_structural_rtlir_gen' ):
      m._pass_structural_rtlir_gen = PassMetadata()

    ns = m._pass_structural_rtlir_gen

    # Generate RTLIR types
    ns.rtlir_type = s.tr_top._rtlir_getter.get_rtlir( m )

    # Generate constants
    ns.consts = []
    rtype = ns.rtlir_type
    const_types = rtype.get_consts_packed()
    for const_name, const_rtype in const_types:
      assert hasattr(m, const_name), \
        f"Internal error: {const_name} is not a member of {m}"
      const_instance = getattr(m, const_name)
      ns.consts.append( ( const_name, const_rtype, const_instance ) )

    # Sort connections
    m_conns_set   = s.inst_conns[m]
    ordered_conns = [ *m.get_connect_order() ]

    # NOTE: this assertion can fail due to connections that
    # are made outside the component that has them. so i'm removing
    # this for now until we can figure out a better way to do sanity
    # check here.
    # assert len(ordered_conns) == len(m_conns_set)

    for i, x in enumerate(ordered_conns):
      if x not in m_conns_set:
        x = (x[1], x[0])
        assert x in m_conns_set, "There is a connection missing from "\
                                 "connect_order. Please contact PyMTL developers!"
        ordered_conns[i] = x

    ns.connections = [ (gen_signal_expr(m, x[0]), gen_signal_expr(m, x[1])) for x in ordered_conns ]
