#=========================================================================
# YosysStructuralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog structural translator."""

from collections import deque

from pymtl3.passes.backends.verilog.errors import VerilogTranslationError
from pymtl3.passes.backends.verilog.translation.structural.VStructuralTranslatorL1 import (
    VStructuralTranslatorL1,
)
from pymtl3.passes.backends.verilog.util.utility import make_indent
from pymtl3.passes.rtlir import RTLIRDataType as rdt


class YosysStructuralTranslatorL1( VStructuralTranslatorL1 ):

  def __init__( s, top ):
    super().__init__( top )
    s.deq = deque()

  #-----------------------------------------------------------------------
  # Connection helper method
  #-----------------------------------------------------------------------

  def vector_conn_gen( s, d, pid, wid, idx, dtype ):
    return [ {
      "direction" : d,
      "pid" : pid,
      "wid" : wid,
      "idx" : idx
    } ]

  def dtype_conn_gen( s, d, pid, wid, idx, dtype ):
    assert isinstance( dtype, rdt.Vector )
    return s.vector_conn_gen( d, pid, wid, idx, dtype )

  def _port_conn_gen( s, d, pid, wid, idx, n_dim, dtype ):
    if not n_dim:
      return s.dtype_conn_gen( d, pid, wid, idx, dtype )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _pid = f"{pid}__{i}"
        _idx = f"{idx}[{i}]"
        ret += s._port_conn_gen( d, _pid, wid, _idx, n_dim[1:], dtype )
      return ret

  def port_connection_gen( s, d, id_, n_dim, dtype ):
    return s._port_conn_gen( d, id_, id_, "", n_dim, dtype )

  #-----------------------------------------------------------------------
  # Port wire declaration helper method
  #-----------------------------------------------------------------------

  def _get_array_dim_str( s, n_dim ):
    ret = "".join( f"[0:{size-1}]" for size in n_dim )
    if ret:
      ret = " " + ret
    return ret

  def wire_vector_gen( s, id_, dtype, n_dim ):
    msb = dtype.get_length() - 1
    return [ {
      "msb" : msb,
      "id_" : id_,
      "n_dim" : n_dim
    } ]

  def wire_dtype_gen( s, id_, dtype, n_dim ):
    assert isinstance( dtype, rdt.Vector )
    s.check_decl( id_, "" )
    return s.wire_vector_gen( id_, dtype, n_dim )

  def port_wire_gen( s, id_, n_dim, dtype ):
    return s.wire_dtype_gen( id_, dtype, n_dim )

  #-----------------------------------------------------------------------
  # Port declaration helper methods
  #-----------------------------------------------------------------------

  def vector_gen( s, d, id_, dtype ):
    direction = d + " " if d else ""
    msb = dtype.get_length() - 1
    return [ {
      "direction" : direction,
      "msb" : msb,
      "id_" : id_
    } ]

  def dtype_gen( s, d, id_, dtype ):
    assert isinstance( dtype, rdt.Vector ), f"unrecognized data type {dtype}"
    s.check_decl( id_, "" )
    return s.vector_gen( d, id_, dtype )

  def port_gen( s, d, id_, n_dim, dtype ):
    if not n_dim:
      return s.dtype_gen( d, id_, dtype )
    else:
      ret = []
      for idx in range(n_dim[0]):
        ret += s.port_gen(d, f"{id_}__{idx}", n_dim[1:], dtype)
      return ret

  #---------------------------------------------------------------------
  # Declarations
  #---------------------------------------------------------------------

  def rtlir_tr_port_decls( s, port_decls ):
    ret = { "port_decls" : [], "wire_decls" : [], "connections" : [] }
    for port_decl in port_decls:
      ret["port_decls"] += port_decl["port_decls"]
      ret["wire_decls"] += port_decl["wire_decls"]
      ret["connections"] += port_decl["connections"]
    make_indent( ret["port_decls"], 1 )
    make_indent( ret["wire_decls"], 1 )
    make_indent( ret["connections"], 1 )
    ret["port_decls"] = ",\n".join( ret["port_decls"] )
    ret["wire_decls"] = "\n".join( ret["wire_decls"] )
    ret["connections"] = "\n".join( ret["connections"] )
    return ret

  def rtlir_tr_port_decl( s, port_id, Type, array_type, _dtype ):
    port_template = "{direction: <7}logic {packed_type: <8} {id_}"
    wire_template = "logic {packed_type: <8} {id_}{array_dim_str};"
    in_conn_template = "assign {wid}{idx} = {pid};"
    out_conn_template = "assign {pid} = {wid}{idx};"

    port_dtype = _dtype['raw_dtype']
    port_direction = Type.get_direction()
    port_n_dim = array_type["n_dim"]
    port_decl, wire_decl, connections = [], [], []

    # Assemble port declarations
    decl_list = s.port_gen( port_direction, port_id, port_n_dim, port_dtype )
    for dct in decl_list:
      direction = dct["direction"]
      msb, id_ = dct["msb"], dct["id_"]
      packed_type = f"[{msb}:0]"
      port_decl.append( port_template.format( **locals() ) )

    # Assemble wire declarations
    decl_list = s.port_wire_gen( port_id, port_n_dim, port_dtype )
    for dct in decl_list:
      msb, id_, n_dim = dct["msb"], dct["id_"], dct["n_dim"]
      array_dim_str = s._get_array_dim_str( n_dim )
      packed_type = f"[{msb}:0]"
      if n_dim or "present" in dct:
        wire_decl.append( wire_template.format( **locals() ) )

    # Assemble connections
    conn_list = s.port_connection_gen( port_direction, port_id, port_n_dim, port_dtype )
    for dct in conn_list:
      direction = dct["direction"]
      pid, wid, idx = dct["pid"], dct["wid"], dct["idx"]
      if idx or "present" in dct:
        if direction.startswith( "input" ):
          connections.append( in_conn_template.format( **locals() ) )
        else:
          connections.append( out_conn_template.format( **locals() ) )

    return {
      "port_decls" : port_decl,
      "wire_decls" : wire_decl,
      "connections" : connections
    }

  def rtlir_tr_wire_decls( s, wire_decls ):
    wires = []
    for wire_decl in wire_decls:
      wires += wire_decl
    make_indent( wires, 1 )
    return '\n'.join( wires )

  def rtlir_tr_wire_decl( s, wire_id, Type, array_type, _dtype ):
    wire_template = "logic {packed_type: <8} {id_}{array_dim_str};"

    wire_dtype = _dtype['raw_dtype']
    wire_n_dim = array_type['n_dim']
    wire_decl = []

    # Assemble wire declarations
    decl_list = s.port_wire_gen( wire_id, wire_n_dim, wire_dtype )
    for dct in decl_list:
      msb, id_ = dct["msb"], dct["id_"]
      array_dim_str = s._get_array_dim_str( dct["n_dim"] )
      packed_type = f"[{msb}:0]"
      wire_decl.append( wire_template.format( **locals() ) )

    return wire_decl

  def rtlir_tr_const_decls( s, const_decls ):
    return ""

  def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
    return ""

  #---------------------------------------------------------------------
  # Connections
  #---------------------------------------------------------------------

  def rtlir_tr_connection( s, wr_signal, rd_signal ):
    # First assemble the WR signal
    sexp = s.deq.popleft()
    all_terms = sexp['attr'] + sexp['index']
    template = sexp['s_attr'] + sexp['s_index']
    wr = template.format( *all_terms )
    # Then assemble the RD signal
    sexp = s.deq.popleft()
    all_terms = sexp['attr'] + sexp['index']
    template = sexp['s_attr'] + sexp['s_index']
    rd = template.format( *all_terms )
    return f"assign {rd} = {wr};"

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_bit_selection( s, base_signal, index, status ):
    # Bit selection
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return f'{base_signal}[{index}]'

  def rtlir_tr_part_selection( s, base_signal, start, stop, status ):
    # Part selection
    _stop = stop-1
    s.deq[-1]['s_index'] += "[{}:{}]"
    s.deq[-1]['index'].append( int(_stop) )
    s.deq[-1]['index'].append( int(start) )
    return f'{base_signal}[{_stop}:{start}]'

  def rtlir_tr_port_array_index( s, base_signal, index, status ):
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return f'{base_signal}[{index}]'

  def rtlir_tr_wire_array_index( s, base_signal, index, status ):
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return f'{base_signal}[{index}]'

  def rtlir_tr_const_array_index( s, base_signal, index, status ):
    assert False, f"constant array {base_signal} is not allowed!"

  def rtlir_tr_current_comp_attr( s, base_signal, attr, status ):
    s.deq[-1]['s_attr'] = attr
    return f'{attr}'

  def rtlir_tr_current_comp( s, comp_id, comp_rtype, status ):
    s.deq.append( {'attr':[], 'index':[], 's_attr':"", 's_index':""} )
    return ''

  def rtlir_tr_literal_number( s, nbits, value, first_called = True ):
    num_str = s._literal_number( nbits, value )
    if first_called:
      s.deq.append( {'attr':[], 'index':[], 's_attr':num_str, 's_index':""} )
    return num_str
