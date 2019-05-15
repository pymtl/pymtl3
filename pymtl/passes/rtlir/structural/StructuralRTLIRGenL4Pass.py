#=========================================================================
# StructuralRTLIRGenL4Pass.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019
"""Provide L4 structural RTLIR generation pass."""

from pymtl.passes.BasePass import PassMetadata
from StructuralRTLIRGenL3Pass import StructuralRTLIRGenL3Pass
from StructuralRTLIRSignalExpr import gen_signal_expr

class StructuralRTLIRGenL4Pass( StructuralRTLIRGenL3Pass ):

  # Override
  def __call__( s, top ):

    s.gen_metadata( top )
    super( StructuralRTLIRGenL4Pass, s ).__call__( top )

  #-----------------------------------------------------------------------
  # gen_metadata
  #-----------------------------------------------------------------------

  def gen_metadata( s, m ):

    if not hasattr( m, '_pass_structural_rtlir_gen' ):

      m._pass_structural_rtlir_gen = PassMetadata()

    for child in m.get_child_components(): s.gen_metadata( child )

  #-----------------------------------------------------------------------
  # gen_rtlir_types
  #-----------------------------------------------------------------------

  # Override
  def gen_rtlir_types( s, m ):

    super( StructuralRTLIRGenL4Pass, s ).gen_rtlir_types( m )

    for child in m.get_child_components(): s.gen_rtlir_types( child )

  #-----------------------------------------------------------------------
  # gen_constants
  #-----------------------------------------------------------------------

  # Override
  def gen_constants( s, m ):

    super( StructuralRTLIRGenL4Pass, s ).gen_constants( m )

    for child in m.get_child_components(): s.gen_constants( child )

  #-----------------------------------------------------------------------
  # add_conn_self_child
  #-----------------------------------------------------------------------

  # Override
  def add_conn_self_child( s, component, writer, reader ):

    ns = s.top._pass_structural_rtlir_gen

    _rw_pair = ( gen_signal_expr( component, writer ),
                 gen_signal_expr( component, reader ) )

    ns.connections_self_child[ component ].add( _rw_pair )

  #-----------------------------------------------------------------------
  # add_conn_child_child
  #-----------------------------------------------------------------------

  # Override
  def add_conn_child_child( s, component, writer, reader ):

    ns = s.top._pass_structural_rtlir_gen

    _rw_pair = ( gen_signal_expr( component, writer ),
                 gen_signal_expr( component, reader ) )

    ns.connections_child_child[ component ].add( _rw_pair )

  #-----------------------------------------------------------------------
  # collect_connections
  #-----------------------------------------------------------------------

  # Override
  def collect_connections( s, m ):

    ns = s.top._pass_structural_rtlir_gen

    return super( StructuralRTLIRGenL4Pass, s ).collect_connections( m )+\
           map( lambda x: ( x, False ), ns.connections_self_child[m] )+\
           map( lambda x: ( x, False ), ns.connections_child_child[m] )

  #-----------------------------------------------------------------------
  # sort_connections
  #-----------------------------------------------------------------------
  # At L4 we need to recursively generate connections for every component

  # Override
  def sort_connections( s, m ):

    super( StructuralRTLIRGenL4Pass, s ).sort_connections( m )

    for child in m.get_child_components(): s.sort_connections( child )

  #-----------------------------------------------------------------------
  # gen_interfaces
  #-----------------------------------------------------------------------

  def gen_interfaces( s, m ):

    super( StructuralRTLIRGenL4Pass, s ).gen_interfaces( m )

    for child in m.get_child_components(): s.gen_interfaces( child )
