#=========================================================================
# StructuralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 24, 2019
"""Provide L1 structural translator."""

from collections import defaultdict, deque

from pymtl3 import Placeholder
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL1Pass import (
    StructuralRTLIRGenL1Pass,
)
from pymtl3.passes.rtlir.util.utility import get_component_full_name

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata


def gen_connections( top ):
  """Return a collections of all connections of each instance in the
     hierarchy whose top is `top`.
  """
  _inst_conns = defaultdict( set )

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
            _inst_conns[writer_host].add( ( u, v ) )
          elif writer_host_parent is reader_host:
            _inst_conns[reader_host].add( ( u, v ) )
          elif writer_host is reader_host_parent:
            _inst_conns[writer_host].add( ( u, v ) )
          elif writer_host_parent == reader_host_parent:
            _inst_conns[writer_host_parent].add( ( u, v ) )
          else:
            raise TypeError( "unexpected connection type!" )

  return _inst_conns

class StructuralTranslatorL1( BaseRTLIRTranslator ):
  def __init__( s, top ):
    super().__init__( top )
    # To avoid doing redundant computation, we generate the connections of
    # the entire hierarchy once and only once here.
    s.inst_conns = gen_connections( top )

  def clear( s, tr_top ):
    super().clear( tr_top )

    # Set dummy tr_cfgs for testing
    if not hasattr( s, 'tr_cfgs' ):
      s.tr_cfgs = None

    # Metadata namespace for RTLIR structural translator and the backend
    # structural translator
    s.structural = TranslatorMetadata()
    s.s_backend = TranslatorMetadata()

    # Generate metadata
    s.gen_structural_trans_metadata( tr_top )

    # Data type declaration
    s.structural.decl_type_vector = {}
    s.structural.decl_type_array  = {}

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  def _get_structural_rtlir_gen_pass( s ):
    return StructuralRTLIRGenL1Pass

  def gen_structural_trans_metadata( s, tr_top ):
    tr_top.apply( s._get_structural_rtlir_gen_pass()( s.inst_conns ) )
    s.structural.component_no_synthesis_no_clk = {}
    s.structural.component_no_synthesis_no_reset = {}
    s._gen_structural_no_clk_reset( tr_top )

  def _gen_structural_no_clk_reset( s, m ):
    if s.tr_cfgs:
      s.structural.component_no_synthesis_no_clk[m] = s.tr_cfgs[m].no_synthesis_no_clk
      s.structural.component_no_synthesis_no_reset[m] = s.tr_cfgs[m].no_synthesis_no_reset
    else:
      s.structural.component_no_synthesis_no_clk[m] = False
      s.structural.component_no_synthesis_no_reset[m] = False
    for _m in m.get_child_components(repr):
      s._gen_structural_no_clk_reset( _m )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  def translate_structural( s, tr_top ):
    """Translate structural part of top component under translation.

    This function will only be called once during the whole translation
    process.
    """
    # Component metadata
    s.structural.component_is_top = {}
    s.structural.component_name = {}
    s.structural.component_file_info = {}
    s.structural.component_full_name = {}
    s.structural.component_unique_name = {}
    s.structural.component_explicit_module_name = {}
    s.structural.component_no_synthesis = {}

    # Declarations
    s.structural.decl_ports  = {}
    s.structural.decl_wires  = {}
    s.structural.decl_consts = {}

    # Placeholder
    s.structural.placeholder_src = {}

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
    m_rtype = m.get_metadata( StructuralRTLIRGenL1Pass.rtlir_type )
    s.structural.component_is_top[m] = m is s.tr_top
    s.structural.component_name[m] = m_rtype.get_name()
    s.structural.component_file_info[m] = m_rtype.get_file_info()
    s.structural.component_full_name[m] = get_component_full_name(m_rtype)
    s.structural.component_unique_name[m] = \
        s.rtlir_tr_component_unique_name(m_rtype)
    if s.tr_cfgs:
      s.structural.component_explicit_module_name[m] = s.tr_cfgs[m].explicit_module_name
    else:
      s.structural.component_explicit_module_name[m] = ''
    if s.tr_cfgs:
      s.structural.component_no_synthesis[m] = s.tr_cfgs[m].no_synthesis
    else:
      s.structural.component_no_synthesis[m] = False

    # Translate declarations of signals
    s.translate_decls( m )

    # Translate connections
    s.translate_connections( m )

    # Grab the pickled external source generated by PlaceholderPass
    s.get_placeholder_src( m )

  #-----------------------------------------------------------------------
  # get_placeholder_src
  #-----------------------------------------------------------------------

  def get_placeholder_src( s, m ):
    if isinstance( m, Placeholder ):
      s.structural.placeholder_src[m] = s.rtlir_tr_placeholder_src( m )
    else:
      s.structural.placeholder_src[m] = ''

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  def translate_decls( s, m ):
    m_rtype  = m.get_metadata( StructuralRTLIRGenL1Pass.rtlir_type )

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

    for const_id, rtype, instance in m.get_metadata( StructuralRTLIRGenL1Pass.consts ):
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
    _connections = m.get_metadata( StructuralRTLIRGenL1Pass.connections )
    for writer, reader in _connections:
      connections.append( s.rtlir_tr_connection(
        s.rtlir_signal_expr_translation( writer, m, 'writer' ),
        s.rtlir_signal_expr_translation( reader, m, 'reader' )
      ) )
    s.structural.connections[m] = s.rtlir_tr_connections( connections )

  #-----------------------------------------------------------------------
  # rtlir_data_type_translation
  #-----------------------------------------------------------------------

  def rtlir_data_type_translation( s, m, dtype ):
    """Translate an RTLIR data type into its backend representation."""
    if isinstance( dtype, ( rdt.Vector, rdt.Bool ) ):
      if isinstance( dtype, rdt.Bool ):
        dtype = rdt.Vector( 1 )
      ret = s.rtlir_tr_vector_dtype( dtype )
      if dtype not in s.structural.decl_type_vector:
        s.structural.decl_type_vector[ dtype ] = ret
      return ret

    else:
      assert False, f"unsupported RTLIR dtype {dtype} at L1!"

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------

  def rtlir_signal_expr_translation( s, expr, m, status = 'intermediate' ):
    """Translate a signal expression in RTLIR into its backend representation.

    Only the following operations are supported at L1:
    sexp.CurComp, sexp.CurCompAttr, sexp.BitSelection, sexp.PartSelection, sexp.PortIndex,
    sexp.WireIndex, sexp.ConstIndex
    """
    if isinstance( expr, sexp.CurComp ):
      comp_id, comp_rtype = expr.get_component_id(), expr.get_rtype()
      return s.rtlir_tr_current_comp( comp_id, comp_rtype, status )

    elif isinstance( expr, sexp.CurCompAttr ):
      return s.rtlir_tr_current_comp_attr(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_attr(), status )

    elif isinstance( expr, sexp.PortIndex ):
      return s.rtlir_tr_port_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index(), status )

    elif isinstance( expr, sexp.WireIndex ):
      return s.rtlir_tr_wire_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index(), status )

    elif isinstance( expr, sexp.ConstIndex ):
      return s.rtlir_tr_const_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index(), status )

    elif isinstance( expr, sexp.BitSelection ):
      base = expr.get_base()
      assert not isinstance(base, (sexp.PartSelection, sexp.BitSelection)), \
        f'bit selection {expr} over bit/part selection {base} is not allowed!'
      return s.rtlir_tr_bit_selection(
        s.rtlir_signal_expr_translation( expr.get_base(), m ), expr.get_index(), status )

    elif isinstance( expr, sexp.PartSelection ):
      base = expr.get_base()
      assert not isinstance(base, (sexp.PartSelection, sexp.BitSelection)), \
        f'part selection {expr} over bit/part selection {base} is not allowed!'
      start, stop = expr.get_slice()[0], expr.get_slice()[1]
      return s.rtlir_tr_part_selection(
        s.rtlir_signal_expr_translation( expr.get_base(), m ), start, stop, status )

    elif isinstance( expr, sexp.ConstInstance ):
      dtype = expr.get_rtype().get_dtype()
      assert isinstance( dtype, rdt.Vector ), \
          f'{dtype} is not supported at L1!'
      return s.rtlir_tr_literal_number( dtype.get_length(), expr.get_value() )

    # Other operations are not supported at L1
    else:
      assert False, f'{expr} is not supported at L1!'

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Placeholder
  def rtlir_tr_placeholder_src( s, m ):
    raise NotImplementedError()

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
  def rtlir_tr_bit_selection( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_part_selection( s, base_signal, start, stop, status ):
    raise NotImplementedError()

  def rtlir_tr_port_array_index( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_wire_array_index( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_const_array_index( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_current_comp_attr( s, base_signal, attr, status ):
    raise NotImplementedError()

  def rtlir_tr_current_comp( s, comp_id, comp_rtype, status ):
    raise NotImplementedError()

  # Miscs
  def rtlir_tr_var_id( s, var_id ):
    raise NotImplementedError()

  def rtlir_tr_literal_number( s, nbits, value ):
    raise NotImplementedError()

  def rtlir_tr_component_unique_name( s, c_rtype ):
    raise NotImplementedError()
