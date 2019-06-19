#=========================================================================
# ImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 14, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""

from __future__ import absolute_import, division, print_function

import os

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.sverilog import ImportPass as SVerilogImportPass
from pymtl3.passes.sverilog.errors import SVerilogImportError
from pymtl3.passes.sverilog.util.utility import get_component_unique_name, make_indent


class ImportPass( SVerilogImportPass ):

  def traverse_hierarchy( s, m ):
    if hasattr(m, "yosys_import") and m.yosys_import:
      return s.do_import( m )
    else:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

  #-----------------------------------------------------------------------
  # get_imported_object
  #-----------------------------------------------------------------------

  def get_imported_object( s, m ):
    rtype = get_component_ifc_rtlir( m )
    full_name = get_component_unique_name( rtype )
    packed_ports = s.gen_packed_ports( rtype )
    dump_vcd = 1 if hasattr( m, "dump_vcd" ) else 0
    try:
      is_same = m._pass_yosys_translation.is_same
    except AttributeError:
      is_same = False

    try:
      sv_file_path = m.yosys_import_path
    except AttributeError:
      sv_file_path = full_name + '.sv'

    # Check if the verilated model is cached
    cached = False
    obj_dir = 'obj_dir_' + full_name
    c_wrapper = full_name + '_v.cpp'
    py_wrapper = full_name + '_v.py'
    shared_lib = 'lib{}_v.so'.format( full_name )
    if is_same and os.path.exists(obj_dir) and os.path.exists(c_wrapper) and \
       os.path.exists(py_wrapper) and os.path.exists(shared_lib):
      cached = True

    assert os.path.isfile( sv_file_path ), \
      "Cannot import {}: {} is not a file!".format( m, sv_file_path )

    s.create_verilator_model( sv_file_path, full_name, dump_vcd, cached )

    c_wrapper_name, port_cdefs = \
        s.create_verilator_c_wrapper( m, full_name, packed_ports, dump_vcd, cached )

    lib_name = \
        s.create_shared_lib( c_wrapper_name, full_name, dump_vcd, cached )

    py_wrapper_name, symbols = \
        s.create_py_wrapper( full_name, rtype, packed_ports,
                           lib_name, port_cdefs, dump_vcd, cached)

    imp = s.import_component( py_wrapper_name, full_name, symbols )

    return imp

  #-------------------------------------------------------------------------
  # Name mangling functions
  #-------------------------------------------------------------------------

  def mangle_vector( s, d, id_, dtype ):
    return [ ( id_, rt.Port( d, dtype ) ) ]

  def mangle_struct( s, d, id_, dtype ):
    ret = []
    all_properties = dtype.get_all_properties()
    for name, field in all_properties:
      ret += s.mangle_dtype( d, id_+"$"+name, field )
    return ret

  def mangle_packed_array( s, d, id_, dtype ):

    def _mangle_packed_array( d, id_, dtype, n_dim ):
      if not n_dim:
        return s.mangle_dtype( d, id_, dtype )
      else:
        ret = []
        for i in range( n_dim[0] ):
          ret += _mangle_packed_array( d, id_+"$__"+str(i), dtype, n_dim[1:] )
        return ret

    n_dim, sub_dtype = dtype.get_dim_sizes(), dtype.get_sub_dtype()
    return _mangle_packed_array( d, id_, sub_dtype, n_dim )

  def mangle_dtype( s, d, id_, dtype ):
    if isinstance( dtype, rdt.Vector ):
      return s.mangle_vector( d, id_, dtype )
    elif isinstance( dtype, rdt.Struct ):
      return s.mangle_struct( d, id_, dtype )
    elif isinstance( dtype, rdt.PackedArray ):
      return s.mangle_packed_array( d, id_, dtype )
    else:
      assert False, "unrecognized data type {}!".format( dtype )
  
  def mangle_port( s, id_, port, n_dim ):
    if not n_dim:
      return s.mangle_dtype( port.get_direction(), id_, port.get_dtype() )
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s.mangle_port( id_+"$__"+str(i), port, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # Python signal connections generation functions
  #-------------------------------------------------------------------------

  def gen_vector_conns( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    _lhs, _rhs = s._verilator_name(lhs), s._verilator_name(rhs)
    ret = ["s.connect( s.{_lhs}, s.mangled__{_rhs} )".format(**locals())]
    return ret, pos + nbits

  def gen_struct_conns( s, d, lhs, rhs, dtype, pos ):
    dtype_name = dtype.get_class().__name__
    upblk_name = lhs.replace('.', '_DOT_').replace('[', '_LBR_').replace(']', '_RBR_')
    ret = [
      "@s.update",
      "def " + upblk_name + "():",
    ]
    if d == "output":
      ret.append( "  s.{lhs} = {dtype_name}()".format( **locals() ) )
    body = []
    all_properties = reversed(dtype.get_all_properties())
    for name, field in all_properties:
      # Use upblk to generate assignment to a struct port
      _ret, pos = s._gen_dtype_conns( d, lhs+"."+name, rhs+"$"+name, field, pos )
      body += _ret
    return ret + body, pos

  def _gen_vector_conns( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    l, r = pos, pos+nbits
    _lhs, _rhs = s._verilator_name( lhs ), s._verilator_name( rhs )
    if d == "input":
      ret = ["  s.mangled__{_rhs} = s.{_lhs}".format( **locals() )]
    else:
      ret = ["  s.{_lhs} = s.mangled__{_rhs}".format( **locals() )]
    return ret, r

  def _gen_struct_conns( s, d, lhs, rhs, dtype, pos ):
    ret = []
    all_properties = reversed(dtype.get_all_properties())
    for name, field in all_properties:
      _ret, pos = s._gen_dtype_conns(d, lhs+"."+name, rhs+"$"+name, field, pos)
      ret += _ret
    return ret, pos

  def _gen_packed_array_conns( s, d, lhs, rhs, dtype, n_dim, pos ):
    if not n_dim:
      return s._gen_dtype_conns( d, lhs, rhs, dtype, pos )
    else:
      ret = []
      for idx in range(n_dim[0]):
        _lhs = lhs + "[{idx}]".format( **locals() )
        _rhs = rhs + "$__{idx}".format( **locals() )
        _ret, pos = \
          s._gen_packed_array_conns( d, _lhs, _rhs, dtype, n_dim[1:], pos )
        ret += _ret
      return ret, pos

  def gen_port_conns( s, id_py, id_v, port, n_dim ):
    if not n_dim:
      d = port.get_direction()
      dtype = port.get_dtype()
      nbits = dtype.get_length()
      ret, pos = s.gen_dtype_conns( d, id_py, id_v, dtype, 0 )
      assert pos == nbits, \
        "internal error: {} wire length mismatch!".format( id_py )
      return ret
    else:
      ret = []
      for idx in range(n_dim[0]):
        _id_py = id_py + "[{idx}]".format( **locals() )
        _id_v = id_v + "$__{idx}".format( **locals() )
        ret += s.gen_port_conns( _id_py, _id_v, port, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # PyMTL combinational input and output generation functions
  #-------------------------------------------------------------------------

  def gen_dtype_comb( s, lhs, rhs, dtype, is_input ):

    def _gen_packed_comb( lhs, rhs, dtype, n_dim, is_input ):
      if not n_dim:
        return s.gen_dtype_comb( lhs, rhs, dtype, is_input )
      else:
        ret = []
        for i in range( n_dim[0] ):
          if is_input:
            _lhs = lhs + "$__" + str(i)
            _rhs = rhs + "[{i}]".format( **locals() )
          else:
            _lhs = lhs + "[{i}]".format( **loacls() )
            _rhs = rhs + "$__" + str(i)
          ret += _gen_packed_comb( _lhs, _rhs, dtype, n_dim[1:] )
        return ret

    if isinstance( dtype, rdt.Vector ):
      nbits = dtype.get_length()
      if is_input:
        return s._gen_ref_write( lhs, rhs, nbits )
      else:
        return s._gen_ref_read( lhs, rhs, nbits )
    elif isinstance( dtype, rdt.Struct ):
      ret = []
      all_properties = dtype.get_all_properties()
      for name, field in all_properties:
        if is_input:
          _lhs = lhs + "$" + name
          _rhs = rhs + "." + name
        else:
          _lhs = lhs + "." + name
          _rhs = rhs + "$" + name
        ret += s.gen_dtype_comb( _lhs, _rhs, field )
      return ret
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return _gen_packed_comb( lhs, rhs, sub_dtype, n_dim, is_input )
    else:
      assert False, "unrecognized data type {}!".format( dtype )

  def gen_port_array_input( s, lhs, rhs, dtype, n_dim ):
    if not n_dim:
      return s.gen_dtype_comb( lhs, rhs, dtype, is_input = True )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _lhs = lhs + "$__{i}".format( **locals() )
        _rhs = rhs + "[{i}]".format( **locals() )
        ret += s.gen_port_array_input( _lhs, _rhs, dtype, n_dim[1:] )
      return ret

  def gen_port_array_output( s, lhs, rhs, dtype, n_dim ):
    if not n_dim:
      return s.gen_dtype_comb( lhs, rhs, dtype, is_input = False )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _lhs = lhs + "[{i}]".format( **locals() )
        _rhs = rhs + "$__{i}".format( **locals() )
        ret += s.gen_port_array_output( _lhs, _rhs, dtype, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # PyMTL wrapper constraint generation function
  #-------------------------------------------------------------------------

  def _gen_constraints( s, name, n_dim, rtype ):
    if not n_dim:
      return ["U( seq_upblk ) < RD( {} ),".format("s.mangled__"+name)]
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s._gen_constraints( name+"$__"+str(i), n_dim[1:], rtype )
      return ret
