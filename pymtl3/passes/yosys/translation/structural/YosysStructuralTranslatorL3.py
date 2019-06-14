#=========================================================================
# YosysStructuralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.structural.SVStructuralTranslatorL3 import (
    SVStructuralTranslatorL3,
)
from pymtl3.passes.sverilog.util.utility import make_indent

from .YosysStructuralTranslatorL2 import YosysStructuralTranslatorL2


class YosysStructuralTranslatorL3(
    YosysStructuralTranslatorL2, SVStructuralTranslatorL3 ):

  #-----------------------------------------------------------------------
  # Helper methods that generate port declarations and connections
  #-----------------------------------------------------------------------

  def ifc_port_gen( s, d, msb, ifc_id, _id, n_dim ):
    template = "{d}logic [{msb}:0] {id_}"
    if not n_dim:
      id_ = ifc_id + "$" + _id
      return [ template.format( **locals() ) ]
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s.ifc_port_gen( d, msb, ifc_id+"$__"+str(i), _id, n_dim[1:] )
      return ret

  def ifc_conn_gen( s, d, cpid, _pid, cwid, _wid, idx, n_dim ):
    if d.startswith( "input" ):
      template = "assign {wid}{idx} = {pid};"
    else:
      template = "assign {pid} = {wid}{idx};"

    if not n_dim:
      pid = cpid + "$" + _pid
      wid = cwid + "$" + _wid
      return [ template.format( **locals() ) ]
    else:
      ret = []
      for i in range( n_dim[0] ):
        _cpid = cpid + "$__" + str(i)
        _idx = "[{}]".format(i) + idx
        ret += s.ifc_conn_gen( d, _cpid, _pid, cwid, _wid, _idx, n_dim[1:] )
      return ret

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def rtlir_tr_interface_port_decls( s, _port_decls ):
    port_decls, wire_decls, connections = [], [], []
    for dct in _port_decls:
      port_decls.append( dct["port_decls"] )
      wire_decls.append( dct["wire_decls"] )
      connections.append( dct["connections"] )
    return {
      "port_decls" : port_decls,
      "wire_decls" : wire_decls,
      "connections" : connections
    }

  def rtlir_tr_interface_port_decl( s, port_id, port_rtype, port_array_type,
      _port_dtype ):
    port_dtype = _port_dtype["raw_dtype"]
    direction = port_rtype.get_direction()
    n_dim = port_array_type["n_dim"]
    port_decl = s.port_gen( direction, port_id, n_dim, port_dtype )
    wire_decl = s.port_wire_gen( port_id, n_dim, port_dtype )
    connections = s.port_connection_gen( direction, port_id, n_dim, port_dtype )
    return {
      "port_decls" : port_decl,
      "wire_decls" : wire_decl,
      "connections" : connections
    }

  def rtlir_tr_interface_decls( s, ifc_decls ):
    port_decls, wire_decls, connections = [], [], []
    for ifc_decl in ifc_decls:
      port_decls += ifc_decl["port_decls"]
      wire_decls += ifc_decl["wire_decls"]
      connections += ifc_decl["connections"]
    make_indent( port_decls, 1 )
    make_indent( wire_decls, 1 )
    make_indent( connections, 1 )
    return {
      "port_decls" : ",\n".join( port_decls ),
      "wire_decls" : "\n".join( wire_decls ),
      "connections" : "\n".join( connections ),
    }

  def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type, ports ):
    ifc_ndim = array_type["n_dim"]
    wire_template = "logic [{msb}:0] {id_}{array_dim_str};"

    # Assemble the interface port declarations
    ret_port = []
    _port_decls = ports["port_decls"]
    for port_decls in _port_decls:
      for port_decl in port_decls:
        direction = port_decl["direction"]
        msb, id_ = port_decl["msb"], port_decl["id_"]
        ret_port += s.ifc_port_gen( direction, msb, ifc_id, id_, ifc_ndim )

    # Assemble the wire declarations
    ret_wire = []
    _wire_decls = ports["wire_decls"]
    for wire_decls in _wire_decls:
      for wire_decl in wire_decls:
        msb, _id, n_dim = wire_decl["msb"], wire_decl["id_"], wire_decl["n_dim"]
        id_ = ifc_id + "$" + _id
        array_dim_str = s._get_array_dim_str( ifc_ndim + n_dim )
        if n_dim or ifc_ndim:
          ret_wire.append( wire_template.format( **locals() ) )

    # Assemble the connections
    ret_connections = []
    if ifc_ndim:
      _connections = ports["connections"]
      for connections in _connections:
        for connection in connections:
          d = connection["direction"]
          pid, wid, idx = connection["pid"], connection["wid"], connection["idx"]
          if idx or ifc_ndim:
            ret_connections += \
              s.ifc_conn_gen( d, ifc_id, pid, ifc_id, wid, idx, ifc_ndim )

    return {
      "port_decls" : ret_port,
      "wire_decls" : ret_wire,
      "connections" : ret_connections
    }

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------
  
  def rtlir_tr_interface_array_index( s, base_signal, index ):
    # Interface array index
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return '{base_signal}[{index}]'.format( **locals() )
  
  def rtlir_tr_interface_attr( s, base_signal, attr ):
    # Interface attribute
    s.deq[-1]['s_attr'] += "${}"
    s.deq[-1]['attr'].append( attr )
    return '{base_signal}.{attr}'.format( **locals() )
