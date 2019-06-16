#=========================================================================
# StructuralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 24, 2019
"""Provide L1 structural translator."""

from __future__ import absolute_import, division, print_function

from collections import defaultdict, deque
from functools import reduce

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL1Pass import (
    StructuralRTLIRGenL1Pass,
)

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata


def gen_connections( top ):
  """Return a tuple of all connections in the hierarchy whose top is `top`.
  
  Return a three element tuple ( ss, sc, cc ). `ss` is a dictionary indexed
  by component `m` and has a set of pairs of connected signals within component
  `m` ( and thus is called "self_self" ). `sc` is a dictionary indexed by
  component `m` and has a set of pairs of connected signals between component
  `m` and its child components ( "self_child" ). `cc` is a dictionary indexed
  by component `m` and has a set of pairs of connected signals between two
  child components of `m` ( "child_child" ).
  """
  _top_conns_self_self = defaultdict( set )
  _top_conns_self_child = defaultdict( set )
  _top_conns_child_child = defaultdict( set )

  nets = top.get_all_value_nets()
  adjs = top.get_signal_adjacency_dict()

  for writer, net in nets:
    S = deque( [ writer ] )
    visited = {  writer  }
    while S:
      u = S.pop()
      writer_host        = u.get_host_component()
      writer_host_parent = writer_host.get_parent_object()
      for v in adjs[u]:
        if v not in visited:
          visited.add( v )
          S.append( v )
          reader_host        = v.get_host_component()
          reader_host_parent = reader_host.get_parent_object()

          # Four possible cases for the reader and writer signals:
          # 1.   They have the same host component. Both need
          #       to be added to the host component.
          # 2/3. One's host component is the parent of the other.
          #       Both need to be added to the parent component.
          # 4.   They have the same parent component.
          #       Both need to be added to the parent component.

          if writer_host is reader_host:
            _top_conns_self_self[writer_host].add( ( u, v ) )
          elif writer_host_parent is reader_host:
            _top_conns_self_child[reader_host].add( ( u, v ) )
          elif writer_host is reader_host_parent:
            _top_conns_self_child[writer_host].add( ( u, v ) )
          elif writer_host_parent == reader_host_parent:
            _top_conns_child_child[writer_host_parent].add( ( u, v ) )
          else:
            assert False, "unexpected connection type!"

  return \
    _top_conns_self_self, _top_conns_self_child, _top_conns_child_child

class StructuralTranslatorL1( BaseRTLIRTranslator ):
  def __init__( s, top ):
    super( StructuralTranslatorL1, s ).__init__( top )
    # To avoid doing redundant computation, we generate the connections of
    # the entire hierarchy once and only once here.
    # c_ss: self-self connections
    # c_sc: self-child connections
    # c_cc: child-child connections
    s.c_ss, s.c_sc, s.c_cc = gen_connections( top )

  def clear( s, tr_top ):
    super( StructuralTranslatorL1, s ).clear( tr_top )
    # Metadata namespace for RTLIR structural translator and the backend
    # structural translator
    s.structural = TranslatorMetadata()
    s.s_backend = TranslatorMetadata()

    # Generate metadata
    s.gen_structural_trans_metadata( tr_top )

    # Data type declaration
    s.structural.decl_type_vector = []
    s.structural.decl_type_array  = []

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  def gen_structural_trans_metadata( s, tr_top ):
    # c_ss: self-self connections
    # c_sc: self-child connections
    # c_cc: child-child connections
    tr_top.apply( StructuralRTLIRGenL1Pass( s.c_ss, s.c_sc, s.c_cc ) )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  def translate_structural( s, tr_top ):
    """Translate structural part of top component under translation.

    This function will only be called once during the whole translation
    process.
    """
    # Component metadata
    s.structural.component_name = {}
    s.structural.component_file_info = {}
    s.structural.component_unique_name = {}

    # Declarations
    s.structural.decl_ports  = {}
    s.structural.decl_wires  = {}
    s.structural.decl_consts = {}

    # Connections
    s.structural.connections = {}
    s._translate_structural( tr_top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------

  def _translate_structural( s, m ):
    """Translate structural part of component m.

    This method will be recursively applied to different components in the
    hierarchy.
    """
    m_rtype = m._pass_structural_rtlir_gen.rtlir_type
    s.structural.component_file_info[m] = m_rtype.get_file_info()
    s.structural.component_name[m] = m_rtype.get_name()
    s.structural.component_unique_name[m] = \
        s.rtlir_tr_component_unique_name(m_rtype)

    # Translate declarations of signals
    s.translate_decls( m )

    # Translate connections
    s.translate_connections( m )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  def translate_decls( s, m ):
    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    # Ports
    port_decls = []
    for port_id, rtype in m_rtype.get_ports_packed():
      if isinstance( rtype, rt.Array ):
        array_type = rtype
        port_rtype = rtype.get_sub_type()
      else:
        array_type = None
        port_rtype = rtype
      port_decls.append(
        s.rtlir_tr_port_decl(
          s.rtlir_tr_var_id( port_id ),
          port_rtype,
          s.rtlir_tr_unpacked_array_type( array_type ),
          s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
      ) )
    s.structural.decl_ports[m] = s.rtlir_tr_port_decls( port_decls )

    # Wires
    wire_decls = []
    for wire_id, rtype in m_rtype.get_wires_packed():
      if isinstance( rtype, rt.Array ):
        array_type = rtype
        wire_rtype = rtype.get_sub_type()
      else:
        array_type = None
        wire_rtype = rtype
      wire_decls.append(
        s.rtlir_tr_wire_decl(
          s.rtlir_tr_var_id( wire_id ),
          wire_rtype,
          s.rtlir_tr_unpacked_array_type( array_type ),
          s.rtlir_data_type_translation( m, wire_rtype.get_dtype() )
      ) )
    s.structural.decl_wires[m] = s.rtlir_tr_wire_decls( wire_decls )

    # Consts
    const_decls = []
    if hasattr( s, "behavioral" ):
      used_set = s.behavioral.accessed[m]
    else:
      used_set = None

    for const_id, rtype, instance in m._pass_structural_rtlir_gen.consts:
      if used_set is None or const_id in used_set:
        if isinstance( rtype, rt.Array ):
          array_type = rtype
          const_rtype = rtype.get_sub_type()
        else:
          array_type = None
          const_rtype = rtype
        const_decls.append(
          s.rtlir_tr_const_decl(
            s.rtlir_tr_var_id( const_id ),
            const_rtype,
            s.rtlir_tr_unpacked_array_type( array_type ),
            s.rtlir_data_type_translation( m, const_rtype.get_dtype() ),
            instance
        ) )
    s.structural.decl_consts[m] = s.rtlir_tr_const_decls( const_decls )

  #-----------------------------------------------------------------------
  # translate_connections
  #-----------------------------------------------------------------------

  def translate_connections( s, m ):
    connections = []
    _connections = m._pass_structural_rtlir_gen.connections
    for writer, reader in _connections:
      connections.append( s.rtlir_tr_connection(
        s.rtlir_signal_expr_translation( writer, m ),
        s.rtlir_signal_expr_translation( reader, m )
      ) )
    s.structural.connections[m] = s.rtlir_tr_connections( connections )

  #-----------------------------------------------------------------------
  # rtlir_data_type_translation
  #-----------------------------------------------------------------------

  def rtlir_data_type_translation( s, m, dtype ):
    """Translate an RTLIR data type into its backend representation."""
    if isinstance( dtype, rdt.Vector ):
      ret = s.rtlir_tr_vector_dtype( dtype )
      if reduce( lambda r, x: r and dtype != x[0],
          s.structural.decl_type_vector, True ):
        s.structural.decl_type_vector.append( ( dtype, ret ) )
      return ret

    else:
      assert False, "unsupported RTLIR dtype {} at L1!".format( dtype )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------

  def rtlir_signal_expr_translation( s, expr, m ):
    """Translate a signal expression in RTLIR into its backend representation.

    Only the following operations are supported at L1:
    sexp.CurComp, sexp.CurCompAttr, sexp.BitSelection, sexp.PartSelection, sexp.PortIndex,
    sexp.WireIndex, sexp.ConstIndex
    """
    if isinstance( expr, sexp.CurComp ):
      comp_id, comp_rtype = expr.get_component_id(), expr.get_rtype()
      return s.rtlir_tr_current_comp( comp_id, comp_rtype )

    elif isinstance( expr, sexp.CurCompAttr ):
      return s.rtlir_tr_current_comp_attr(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_attr() )

    elif isinstance( expr, sexp.PortIndex ):
      return s.rtlir_tr_port_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    elif isinstance( expr, sexp.WireIndex ):
      return s.rtlir_tr_wire_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    elif isinstance( expr, sexp.ConstIndex ):
      return s.rtlir_tr_const_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    elif isinstance( expr, sexp.BitSelection ):
      base = expr.get_base()
      assert not isinstance(base, (sexp.PartSelection, sexp.BitSelection)), \
        'bit selection {} over bit/part selection {} is not allowed!'.format(expr, base)
      return s.rtlir_tr_bit_selection(
        s.rtlir_signal_expr_translation( expr.get_base(), m ), expr.get_index() )

    elif isinstance( expr, sexp.PartSelection ):
      base = expr.get_base()
      assert not isinstance(base, (sexp.PartSelection, sexp.BitSelection)), \
        'part selection {} over bit/part selection {} is not allowed!'.format(expr, base)
      start, stop = expr.get_slice()[0], expr.get_slice()[1]
      return s.rtlir_tr_part_selection(
        s.rtlir_signal_expr_translation( expr.get_base(), m ), start, stop )

    elif isinstance( expr, sexp.ConstInstance ):
      dtype = expr.get_rtype().get_dtype()
      assert isinstance( dtype, rdt.Vector ), \
          '{} is not supported at L1!'.format( dtype )
      return s.rtlir_tr_literal_number( dtype.get_length(), expr.get_value() )

    # Other operations are not supported at L1
    else:
      assert False, '{} is not supported at L1!'.format( expr )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Data types
  def rtlir_tr_vector_dtype( s, Type ):
    raise NotImplementedError()

  def rtlir_tr_unpacked_array_type( s, Type ):
    raise NotImplementedError()

  # Declarations
  def rtlir_tr_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_port_decl( s, id_, rtype, array_type, dtype ):
    raise NotImplementedError()

  def rtlir_tr_wire_decls( s, wire_decls ):
    raise NotImplementedError()

  def rtlir_tr_wire_decl( s, id_, Type, array_type, dtype ):
    raise NotImplementedError()

  def rtlir_tr_const_decls( s, const_decls ):
    raise NotImplementedError()

  def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
    raise NotImplementedError()

  # Connections
  def rtlir_tr_connections( s, connections ):
    raise NotImplementedError()

  def rtlir_tr_connection( s, wr_signal, rd_signal ):
    raise NotImplementedError()

  # Signal operations
  def rtlir_tr_bit_selection( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_part_selection( s, base_signal, start, stop ):
    raise NotImplementedError()

  def rtlir_tr_port_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_wire_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_const_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_current_comp_attr( s, base_signal, attr ):
    raise NotImplementedError()

  def rtlir_tr_current_comp( s, comp_id, comp_rtype ):
    raise NotImplementedError()

  # Miscs
  def rtlir_tr_var_id( s, var_id ):
    raise NotImplementedError()

  def rtlir_tr_literal_number( s, nbits, value ):
    raise NotImplementedError()

  def rtlir_tr_component_unique_name( s, c_rtype ):
    raise NotImplementedError()
