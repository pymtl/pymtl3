#=========================================================================
# StructuralRTLIRGenL4Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 3, 2019
"""Provide L4 structural RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

from pymtl.passes.BasePass import PassMetadata

from .StructuralRTLIRGenL3Pass import StructuralRTLIRGenL3Pass
from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL4Pass( StructuralRTLIRGenL3Pass ):
  # Override
  def __call__( s, top ):
    s.gen_metadata( top )
    super( StructuralRTLIRGenL4Pass, s ).__call__( top )

  def gen_metadata( s, m ):
    if not hasattr( m, '_pass_structural_rtlir_gen' ):
      m._pass_structural_rtlir_gen = PassMetadata()
    for child in m.get_child_components():
      s.gen_metadata( child )

  # Override
  def gen_rtlir_types( s, m ):
    super( StructuralRTLIRGenL4Pass, s ).gen_rtlir_types( m )
    for child in m.get_child_components():
      s.gen_rtlir_types( child )

  # Override
  def gen_constants( s, m ):
    super( StructuralRTLIRGenL4Pass, s ).gen_constants( m )
    for child in m.get_child_components():
      s.gen_constants( child )

  # Override
  def add_conn_self_child( s, component, writer, reader ):
    ns = s.top._pass_structural_rtlir_gen
    _rw_pair = ( gen_signal_expr( component, writer ),
                 gen_signal_expr( component, reader ) )
    ns.connections_self_child[ component ].add( _rw_pair )

  # Override
  def add_conn_child_child( s, component, writer, reader ):
    ns = s.top._pass_structural_rtlir_gen
    _rw_pair = ( gen_signal_expr( component, writer ),
                 gen_signal_expr( component, reader ) )
    ns.connections_child_child[ component ].add( _rw_pair )

  # Override
  def collect_connections( s, m ):
    ns = s.top._pass_structural_rtlir_gen
    return super( StructuralRTLIRGenL4Pass, s ).collect_connections( m )+ \
           map( lambda x: ( x, False ), ns.connections_self_child[m] )+ \
           map( lambda x: ( x, False ), ns.connections_child_child[m] )

  # Override
  def sort_connections( s, m ):
    """Sort connections by the order `s.connect` is called.

    At L4 we need to recursively generate connections for every component.
    """
    super( StructuralRTLIRGenL4Pass, s ).sort_connections( m )
    for child in m.get_child_components():
      s.sort_connections( child )
