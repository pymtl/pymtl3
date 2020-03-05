#=========================================================================
# YosysStructuralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog structural translator."""

from pymtl3.passes.backends.verilog.errors import VerilogTranslationError
from pymtl3.passes.backends.verilog.translation.structural.VStructuralTranslatorL4 import (
    VStructuralTranslatorL4,
)
from pymtl3.passes.backends.verilog.util.utility import make_indent

from .YosysStructuralTranslatorL3 import YosysStructuralTranslatorL3


class YosysStructuralTranslatorL4(
    YosysStructuralTranslatorL3, VStructuralTranslatorL4 ):

  #---------------------------------------------------------------------
  # Declarations
  #---------------------------------------------------------------------

  def rtlir_tr_subcomp_port_decls( s, port_decls ):
    return s.rtlir_tr_interface_port_decls( port_decls )

  def rtlir_tr_subcomp_port_decl( s, m, c_id, c_rtype, c_array_type, port_id,
      port_rtype, port_dtype, port_array_type ):
    return s.rtlir_tr_interface_port_decl(
        m, port_id, port_rtype, port_array_type )

  def rtlir_tr_subcomp_ifc_port_decls( s, ifc_port_decls ):
    return s.rtlir_tr_interface_port_decls( ifc_port_decls )

  def rtlir_tr_subcomp_ifc_port_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, port_id, port_rtype,
      port_array_type ):
    return s.rtlir_tr_interface_port_decl(
        m, port_id, port_rtype, port_array_type )

  def rtlir_tr_subcomp_ifc_decls( s, ifc_decls ):
    port_decls, wire_decls, connections = [], [], []
    for ifc_decl in ifc_decls:
      port_decls += ifc_decl["port_decls"]
      wire_decls += ifc_decl["wire_decls"]
      connections += ifc_decl["connections"]
    return {
      "port_decls" : port_decls,
      "wire_decls" : wire_decls,
      "connections" : connections
    }

  def rtlir_tr_subcomp_ifc_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, ports ):

    def _subcomp_ifc_port_gen( d, msb, ifc_id, id_, n_dim ):
      if not n_dim:
        return [ { "direction" : d, "msb" : msb, "id_" : ifc_id + "__" + id_ } ]
      else:
        ret = []
        for i in range( n_dim[0] ):
          ret += \
            _subcomp_ifc_port_gen( d, msb, ifc_id+"__"+str(i), id_, n_dim[1:] )
        return ret

    def _subcomp_ifc_conn_gen( d, cpid, _pid, cwid, _wid, idx, n_dim ):
      if not n_dim:
        pid = cpid + "__" + _pid
        wid = cwid + "__" + _wid
        return [ { "direction" : d, "pid" : pid, "wid" : wid, "idx" : idx } ]
      else:
        ret = []
        for i in range( n_dim[0] ):
          _cpid = f"{cpid}__{i}"
          _idx = f"[{i}]{idx}"
          ret += \
            _subcomp_ifc_conn_gen( d, _cpid, _pid, cwid, _wid, _idx, n_dim[1:] )
        return ret

    ifc_n_dim = ifc_array_type["n_dim"]
    port_decl, wire_decl, connections = [], [], []

    # Add interface info to port declarations
    for port in ports["port_decls"]:
      for _port in port:
        d = _port["direction"]
        msb, id_ = _port["msb"], _port["id_"]
        port_decl += _subcomp_ifc_port_gen( d, msb, ifc_id, id_, ifc_n_dim )

    # Add interface info to wire declarations
    for wire in ports["wire_decls"]:
      for _wire in wire:
        present = "present" in _wire
        msb, _id, n_dim = _wire["msb"], _wire["id_"], _wire["n_dim"]
        id_ = ifc_id + "__" + _id
        dct = { "msb" : msb, "id_" : id_, "n_dim" : ifc_n_dim+n_dim }
        if present:
          dct["present"] = True
        wire_decl.append( dct )

    # Add interface info to connections
    for conn in ports["connections"]:
      for _conn in conn:
        present = "present" in _conn
        d = _conn["direction"]
        pid, wid, idx = _conn["pid"], _conn["wid"], _conn["idx"]
        dct_list = \
          _subcomp_ifc_conn_gen( d, ifc_id, pid, ifc_id, wid, idx, ifc_n_dim )
        if present:
          for dct in dct_list:
            dct["present"] = True
        connections += dct_list

    return {
      "port_decls" : port_decl,
      "wire_decls" : wire_decl,
      "connections" : connections
    }

  def rtlir_tr_subcomp_decls( s, subcomp_decls ):
    port_decls, wire_decls, conns = [], [], []
    for subcomp_decl in subcomp_decls:
      port_decls.extend( subcomp_decl["port_decls"] )
      wire_decls.extend( subcomp_decl["wire_decls"] )
      conns.extend( subcomp_decl["connections"] )
    make_indent( wire_decls, 1 )
    make_indent( conns, 1 )
    return {
      "port_decls" : "\n\n".join( port_decls ),
      "wire_decls" : "\n".join( wire_decls ),
      "connections" : "\n".join( conns )
    }

  def rtlir_tr_subcomp_decl( s, m, c_id, c_rtype, c_array_type, port_conns, ifc_conns ):

    def _subcomp_port_gen( c_name, c_id, n_dim, port_decls ):
      p_wire_tplt = "logic {packed_type: <8} {id_};"
      p_conn_tplt = ".{port_id: <15}( {port_wire_id} )"
      template = \
"""\
{port_wires}

  {c_name} {c_id}
  (
{port_conn_decls}
  );\
"""
      if not n_dim:
        p_wires, p_conns = [], []
        for port in port_decls:
          msb, _id = port["msb"], port["id_"]
          id_ = c_id + "__" + _id
          port_id = _id
          port_wire_id = ( f"{c_id}__{_id}" ).center( 25 )
          packed_type = f"[{msb}:0]"
          p_wires.append( p_wire_tplt.format( **locals() ) )
          p_conns.append( p_conn_tplt.format( **locals() ) )
        make_indent( p_wires, 1 )
        make_indent( p_conns, 2 )
        port_wires = "\n".join( p_wires )
        port_conn_decls = ",\n".join( p_conns )
        return [ template.format( **locals() ) ]
      else:
        ret = []
        for i in range( n_dim[0] ):
          ret += _subcomp_port_gen( c_name, c_id+"__"+str(i), n_dim[1:], port_decls )
        return ret

    def _subcomp_conn_gen( d, cpid, _pid, cwid, _wid, idx, n_dim ):
      if d.startswith( "input" ):
        template = "assign {pid} = {wid}{idx};"
      else:
        template = "assign {wid}{idx} = {pid};"
      if not n_dim:
        pid = f"{cpid}__{_pid}"
        wid = f"{cwid}__{_wid}"
        return [ template.format( **locals() ) ]
      else:
        ret = []
        for i in range( n_dim[0] ):
          _cpid = f"{cpid}__{i}"
          _idx = f"[{i}]{idx}"
          ret += _subcomp_conn_gen( d, _cpid, _pid, cwid, _wid, _idx, n_dim[1:] )
        return ret

    wire_template = "logic {packed_type: <8} {id_}{array_dim_str};"
    _port_decls, _wire_decls, _connections = [], [], []

    for port_decl in port_conns["port_decls"]:
      _port_decls += port_decl
    _port_decls += ifc_conns["port_decls"]

    for wire_decl in port_conns["wire_decls"]:
      _wire_decls += wire_decl
    _wire_decls += ifc_conns["wire_decls"]

    for conn in port_conns["connections"]:
      _connections += conn
    _connections += ifc_conns["connections"]

    port_decls, wire_decls, connections = [], [], []

    c_n_dim = c_array_type["n_dim"]

    # Add sub-component info to port declarations and generate declarations
    c_name = s.rtlir_tr_component_unique_name( c_rtype )
    port_decls = _subcomp_port_gen( c_name, c_id, c_n_dim, _port_decls )

    # Add sub-component info to wire declarations and generate declarations
    for wire in _wire_decls:
      msb, _id, n_dim = wire["msb"], wire["id_"], wire["n_dim"]
      id_ = c_id + "__" + _id
      array_dim_str = s._get_array_dim_str( c_n_dim + n_dim )
      packed_type = f"[{msb}:0]"
      if c_n_dim or n_dim or "present" in wire:
        wire_decls.append( wire_template.format( **locals() ) )

    # Add sub-component info to connections and generate connections
    for _conn in _connections:
      d, pid, wid, idx = _conn["direction"], _conn["pid"], _conn["wid"], _conn["idx"]
      if c_n_dim or idx or "present" in _conn:
        connections += _subcomp_conn_gen( d, c_id, pid, c_id, wid, idx, c_n_dim )

    return {
      "port_decls" : port_decls,
      "wire_decls" : wire_decls,
      "connections" : connections
    }

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_component_array_index( s, base_signal, index, status ):
    # Component array index
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return f'{base_signal}[{index}]'

  def rtlir_tr_subcomp_attr( s, base_signal, attr, status ):
    # Sub-component attribute
    s.deq[-1]['s_attr'] += "__{}"
    s.deq[-1]['attr'].append( attr )
    return f'{base_signal}.{attr}'
