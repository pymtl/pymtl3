#=========================================================================
# StructuralRTLIRGenL1Pass.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019
"""Provide L1 structural RTLIR generation pass."""

from pymtl3 import MetadataKey
from pymtl3.passes.PlaceholderConfigs import PlaceholderConfigs
# from pymtl3.passes.rtlir.RTLIRPass import RTLIRPass
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype.RTLIRType import RTLIRGetter

from .StructuralRTLIRGenL0Pass import StructuralRTLIRGenL0Pass
from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL1Pass( StructuralRTLIRGenL0Pass ):

  def __init__( s, inst_conns ):
    s.inst_conns = inst_conns

  def __call__( s, tr_top ):
    """ generate structural RTLIR for component `tr_top` """
    c = s.__class__
    s.tr_top = tr_top
    if not tr_top.has_metadata( c.rtlir_getter ):
      tr_top.set_metadata( c.rtlir_getter, RTLIRGetter(cache=True) )

    try:
      s._gen_metadata( tr_top )
    except AssertionError as e:
      msg = '' if not e.args is None else e.args[0]
      raise RTLIRConversionError( tr_top, msg )

  def _gen_metadata( s, m ):
    c = s.__class__

    # Generate RTLIR types
    rtlir_type = s.tr_top.get_metadata( c.rtlir_getter ).get_rtlir( m )
    m.set_metadata( c.rtlir_type, rtlir_type )

    # Generate constants
    consts = []
    rtype = rtlir_type
    const_types = rtype.get_consts_packed()
    for const_name, const_rtype in const_types:
      assert hasattr(m, const_name), \
        f"Internal error: {const_name} is not a member of {m}"
      const_instance = getattr(m, const_name)
      consts.append( ( const_name, const_rtype, const_instance ) )

    m.set_metadata( c.consts, consts )

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

    connections = [ (gen_signal_expr(m, x[0]), gen_signal_expr(m, x[1])) for x in ordered_conns ]

    m.set_metadata( c.connections, connections )
