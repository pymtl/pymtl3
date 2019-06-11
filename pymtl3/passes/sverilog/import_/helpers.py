#=========================================================================
# helpers.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 30, 2019
"""Provide helper methods to the SystemVerilog import pass."""

from __future__ import absolute_import, division, print_function

import copy
from functools import reduce

from pymtl3.datatypes import Bits, BitStruct, mk_bits
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.util.utility import make_indent

#-------------------------------------------------------------------------
# Internal helper methods
#-------------------------------------------------------------------------

def _verilator_name( name ):
  return name.replace('__', '___05F').replace('$', '__024')

def _get_direction( port ):
  if isinstance( port, rt.Port ):
    d = port.get_direction()
  elif isinstance( port, rt.Array ):
    d = port.get_sub_type().get_direction()
  else:
    assert False, "{} is not a port or array of ports!".format( port )
  if d == 'input':
    return 'InPort'
  elif d == 'output':
    return 'OutPort'
  else:
    assert False, "unrecognized direction {}!".format( d )

def _get_bit_width( port ):
  if isinstance( port, rt.Array ):
    nbits = port.get_sub_type().get_dtype().get_length()
  else:
    nbits = port.get_dtype().get_length()
  if    nbits <= 8:  return 8
  elif  nbits <= 16: return 16
  elif  nbits <= 32: return 32
  elif  nbits <= 64: return 64
  else:              return 32

def _get_c_n_dim( port ):
  if isinstance( port, rt.Array ):
    return port.get_dim_sizes()
  else:
    return []

def _get_c_dim( port ):
  return reduce(lambda s, i: s+"[{}]".format(i), _get_c_n_dim(port), "")

def _get_c_nbits( port ):
  if isinstance( port, rt.Array ):
    dtype = port.get_sub_type().get_dtype()
  else:
    dtype = port.get_dtype()
  return dtype.get_length()

def _gen_ref_write( lhs, rhs, nbits ):
  if nbits <= 64:
    return [ "{lhs}[0] = int({rhs})".format( **locals() ) ]
  else:
    ret = []
    ITEM_BITWIDTH = 32
    num_assigns = (nbits-1)//ITEM_BITWIDTH+1
    for idx in range(num_assigns):
      l = ITEM_BITWIDTH*idx
      r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
      ret.append("{lhs}[{idx}] = int({rhs}[{l}:{r}])".format(**locals()))
    return ret

def _gen_ref_read( lhs, rhs, nbits ):
  if nbits <= 64:
    return [ "{lhs} = Bits{nbits}({rhs}[0])".format( **locals() ) ]
  else:
    ret = []
    ITEM_BITWIDTH = 32
    num_assigns = (nbits-1)//ITEM_BITWIDTH+1
    for idx in range(num_assigns):
      l = ITEM_BITWIDTH*idx
      r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
      _nbits = r - l
      ret.append("{lhs}[{l}:{r}] = Bits{_nbits}({rhs}[{idx}])".format(**locals()))
    return ret

def _is_of_port( rtype ):
  if isinstance(rtype, rt.Port):
    return True
  if isinstance(rtype, rt.Array) and isinstance(rtype.get_sub_type(), rt.Port):
    return True
  return False

#-------------------------------------------------------------------------
# gen_packed_ports
#-------------------------------------------------------------------------

def gen_packed_ports( rtype ):
  """Return a list of (name, rt.Port ) that has all ports of `rtype`.
  
  This method performs SystemVerilog backend-specific name mangling and
  returns all ports that appear in the interface of component `rtype`.
  Each tuple contains a port or an array of port that has any data type
  allowed in RTLIRDataType.
  """

  def _mangle_port( id_, port ):
    return [ ( id_, port ) ]

  def _mangle_interface( id_, _ifc ):
    def _gen_single_ifc( id_, ifc ):
      ret = []
      all_properties = ifc.get_all_properties_packed()
      for prop_name, prop_rtype in all_properties:
        if _is_of_port( prop_rtype ):
          ret += _mangle_port( id_+'$'+prop_name, prop_rtype )
        else:
          ret += _mangle_interface( id_+'$'+prop_name, prop_rtype )
      return ret
    def _gen_ifc( id_, ifc, n_dim ):
      if not n_dim:
        return _gen_single_ifc( id_, ifc )
      else:
        ret = []
        for idx in range( n_dim[0] ):
          ret += _gen_ifc( id_+"$__"+str(idx), ifc, n_dim[1:] )
        return ret
    if isinstance( _ifc, rt.Array ):
      ifc = _ifc.get_sub_type()
      n_dim = _ifc.get_dim_sizes()
    else:
      ifc = _ifc
      n_dim = []
    return _gen_ifc( id_, ifc, n_dim )

  packed_ports = []
  ports = rtype.get_ports_packed()
  ifcs = rtype.get_ifc_views_packed()
  for id_, port in ports:
    packed_ports += _mangle_port( id_, port )
  for id_, ifc in ifcs:
    packed_ports += _mangle_interface( id_, ifc )
  return packed_ports

#-------------------------------------------------------------------------
# gen_signal_decl_c
#-------------------------------------------------------------------------

def gen_signal_decl_c( name, port ):
  """Return C variable declaration of `port`."""
  c_dim = _get_c_dim( port )
  nbits = _get_c_nbits( port )
  if    nbits <= 8:  data_type = 'unsigned char'
  elif  nbits <= 16: data_type = 'unsigned short'
  elif  nbits <= 32: data_type = 'unsigned int'
  elif  nbits <= 64: data_type = 'unsigned long'
  else:              data_type = 'unsigned int'
  name = _verilator_name( name )
  return '{data_type} * {name}{c_dim};'.format( **locals() )

#-------------------------------------------------------------------------
# gen_signal_init_c
#-------------------------------------------------------------------------

def gen_signal_init_c( name, port ):
  """Return C port variable initialization."""
  ret       = []
  c_dim     = _get_c_dim( port )
  nbits     = _get_c_nbits( port )
  deference = '&' if nbits <= 64 else ''
  name      = _verilator_name( name )

  if c_dim:
    n_dim_size = _get_c_n_dim( port )
    sub = ""
    for_template = \
"""\
for ( int i_{idx} = 0; i_{idx} < {dim_size}; i_{idx}++ )
"""
    assign_template = \
"""\
m->{name}{sub} = {deference}model->{name}{sub};
"""

    for idx, dim_size in enumerate( n_dim_size ):
      ret.append( for_template.format( **locals() ) )
      sub += "[i_{idx}]".format( **locals() )

    ret.append( assign_template.format( **locals() ) )

    # Indent the for loop
    for start, dim_size in enumerate( n_dim_size ):
      for idx in range( start + 1, len( n_dim_size ) + 1 ):
        ret[ idx ] = "  " + ret[ idx ]

  else:
    ret.append('m->{name} = {deference}model->{name};'.format(**locals()))

  return ret

#-------------------------------------------------------------------------
# gen_signal_decl_py
#-------------------------------------------------------------------------

def gen_signal_decl_py( rtype ):
  """Return the PyMTL definition of all interface ports of `rtype`."""

  #-----------------------------------------------------------------------
  # Methods that generate signal declarations
  #-----------------------------------------------------------------------

  def gen_dtype_str( symbols, dtype ):
    if isinstance( dtype, rdt.Vector ):
      nbits = dtype.get_length()
      Bits_name = "Bits{nbits}".format( **locals() )
      if Bits_name not in symbols and nbits >= 256:
        Bits_class = mk_bits( nbits )
        symbols.update( { Bits_name : Bits_class } )
      return 'Bits{}'.format( dtype.get_length() )
    elif isinstance( dtype, rdt.Struct ):
      # It is possible to reuse the existing struct class because its __init__
      # can be called without arguments.
      name, cls = dtype.get_name(), dtype.get_class()
      if name not in symbols:
        symbols.update( { name : cls } )
      return name
    else:
      assert False, "unrecognized data type {}!".format( dtype )

  def gen_port_decl_py( ports ):
    symbols, decls = {}, []
    for id_, _port in ports:
      if id_ not in ['clk', 'reset']:
        if isinstance( _port, rt.Array ):
          n_dim = _port.get_dim_sizes()
          rhs = "{direction}( {dtype} )"
          port = _port.get_sub_type()
          _n_dim = copy.copy( n_dim )
          _n_dim.reverse()
          for length in _n_dim:
            rhs = "[ " + rhs + (" for _ in range({length}) ]".format(**locals()))
        else:
          rhs = "{direction}( {dtype} )"
          port = _port
        direction = _get_direction( port )
        dtype = gen_dtype_str( symbols, port.get_dtype() )
        rhs = rhs.format( **locals() )
        decls.append("s.{id_} = {rhs}".format(**locals()))
    return symbols, decls

  def gen_ifc_decl_py( ifcs ):

    def gen_ifc_str( symbols, ifc ):

      def _get_arg_str( name, obj ):
        if isinstance( obj, int ):
          return str(obj)
        elif isinstance( obj, Bits ):
          nbits = obj.nbits
          value = obj.value
          Bits_name = "Bits{nbits}".format( **locals() )
          Bits_arg_str = "{Bits_name}( {value} )".format( **locals() )
          if Bits_name not in symbols and nbits >= 256:
            Bits_class = mk_bits( nbits )
            symbols.update( { Bits_name : Bits_class } )
          return Bits_arg_str
        elif isinstance( obj, BitStruct ):
          # This is hacky: we don't know how to construct an object that
          # is the same as `obj`, but we do have the object itself. If we
          # add `obj` to the namespace of `construct` everything works fine
          # but the user cannot tell what object is passed to the constructor
          # just from the code.
          bs_name = "_"+name+"_obj"
          if bs_name not in symbols:
            symbols.update( { bs_name : obj } )
          return bs_name
        elif isinstance( obj, type ) and issubclass( obj, Bits ):
          nbits = obj.nbits
          Bits_name = "Bits{nbits}".format( **locals() )
          if Bits_name not in symbols and nbits >= 256:
            Bits_class = mk_bits( nbits )
            symbols.update( { Bits_name : Bits_class } )
          return Bits_name
        elif isinstance( obj, type ) and issubclass( obj, BitStruct ):
          BitStruct_name = obj.__name__
          if BitStruct_name not in symbols:
            symbols.update( { BitStruct_name : obj } )
          return BitStruct_name
        else:
          assert False, \
            "Interface constructor argument {} is not an int/Bits/BitStruct!". \
              format( obj )

      name, cls = ifc.get_name(), ifc.get_class()
      if name not in symbols:
        symbols.update( { name : cls } )
      arg_list = []
      args = ifc.get_args()
      for idx, obj in enumerate(args[0]):
        arg_list.append( _get_arg_str( "_ifc_arg"+str(idx), obj ) )
      for arg_name, arg_obj in args[1].iteritems():
        arg_list.append( arg_name + " = " + _get_arg_str( arg_name, arg_obj ) )
      return name, ', '.join( arg_list )

    symbols, decls = {}, []
    for id_, ifc in ifcs:
      if isinstance( ifc, rt.Array ):
        n_dim = ifc.get_dim_sizes()
        rhs = "{ifc_class}({ifc_params})"
        _ifc = ifc.get_sub_type()
        _n_dim = copy.copy( n_dim )
        _n_dim.reverse()
        for length in _n_dim:
          rhs = "[ " + rhs + (" for _ in range({length}) ]".format(**locals()))
      else:
        rhs = "{ifc_class}({ifc_params})"
        _ifc = ifc
      ifc_class, ifc_params = gen_ifc_str( symbols, _ifc )
      if ifc_params:
        ifc_params = " " + ifc_params + " "
      rhs = rhs.format( **locals() )
      decls.append("s.{id_} = {rhs}".format(**locals()))
    return symbols, decls

  #-----------------------------------------------------------------------
  # Methods that generate signal connections
  #-----------------------------------------------------------------------
  # Ports and interfaces will have the same name; their name-mangled
  # counterparts will have a mangled name starting with 'mangled__'.

  def gen_packed_array_conns( lhs, rhs, dtype, n_dim, pos ):
    if not n_dim:
      return gen_dtype_conns( lhs, rhs, dtype, pos )
    else:
      ret = []
      for idx in range(n_dim[0]):
        _lhs = lhs + "[{idx}]".format( **locals() )
        _ret, pos = \
          gen_packed_array_conns( _lhs, rhs, dtype, n_dim[1:], pos )
        ret += _ret
      return ret, pos

  def gen_dtype_conns( lhs, rhs, dtype, pos ):
    if isinstance( dtype, rdt.Vector ):
      nbits = dtype.get_length()
      l, r = pos, pos+nbits
      _lhs, _rhs = _verilator_name(lhs), _verilator_name(rhs)
      ret = ["s.connect( s.{_lhs}, s.mangled__{_rhs}[{l}:{r}] )".format(**locals())]
      return ret, r
    elif isinstance( dtype, rdt.Struct ):
      ret = []
      all_properties = reversed(dtype.get_all_properties())
      for field_name, field in all_properties:
        _ret, pos = gen_dtype_conns( lhs+"."+field_name, rhs, field, pos )
        ret += _ret
      return ret, pos
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      _dtype = dtype.get_sub_dtype()
      return gen_packed_array_conns( lhs, rhs, _dtype, n_dim, pos )
    else:
      assert False, "unrecognized data type {}!".format( dtype )

  def gen_port_conns( id_py, id_v, _port ):

    def _gen_port_conns( id_py, id_v, port, n_dim ):
      if not n_dim:
        dtype = port.get_dtype()
        nbits = dtype.get_length()
        ret, pos = gen_dtype_conns( id_py, id_v, dtype, 0 )
        assert pos == nbits, \
          "internal error: {} wire length mismatch!".format( id_py )
        return ret
      else:
        ret = []
        for idx in range(n_dim[0]):
          _id_py = id_py + "[{idx}]".format( **locals() )
          _id_v = id_v + "[{idx}]".format( **locals() )
          ret += _gen_port_conns( _id_py, _id_v, port, n_dim[1:] )
        return ret

    if isinstance( _port, rt.Array ):
      n_dim = _port.get_dim_sizes()
      port = _port.get_sub_type()
    else:
      n_dim = []
      port = _port
    return _gen_port_conns( id_py, id_v, port, n_dim )

  def gen_ifc_conns( id_py, id_v, _ifc ):

    def _gen_single_ifc_conn( id_py, id_v, ifc ):
      ret = []
      all_properties = ifc.get_all_properties_packed()
      for prop_name, prop_rtype in all_properties:
        _id_py = id_py + ".{prop_name}".format( **locals() )
        _id_v = id_v + "${prop_name}".format( **locals() )
        if _is_of_port( prop_rtype ):
          ret += gen_port_conns( _id_py, _id_v, prop_rtype )
        else:
          ret += gen_ifc_conns( _id_py, _id_v, prop_rtype )
      return ret

    def _gen_ifc_conns( id_py, id_v, ifc, n_dim ):
      if not n_dim:
        return _gen_single_ifc_conn( id_py, id_v, ifc )
      else:
        ret = []
        for idx in range( n_dim[0] ):
          _id_py = id_py + "[{idx}]".format( **locals() )
          _id_v = id_v + "$__{idx}".format( **locals() )
          ret += _gen_ifc_conns( _id_py, _id_v, ifc, n_dim[1:] )
        return ret

    if isinstance( _ifc, rt.Array ):
      n_dim = _ifc.get_dim_sizes()
      ifc = _ifc.get_sub_type()
    else:
      n_dim = []
      ifc = _ifc
    return _gen_ifc_conns( id_py, id_v, ifc, n_dim )

  #-----------------------------------------------------------------------
  # Method gen_signal_decl_py
  #-----------------------------------------------------------------------

  ports = rtype.get_ports_packed()
  ifcs = rtype.get_ifc_views_packed()

  p_symbols, p_decls = gen_port_decl_py( ports )
  i_symbols, i_decls = gen_ifc_decl_py( ifcs )

  p_conns, i_conns = [], []
  for id_, port in ports:
    p_conns += gen_port_conns( id_, id_, port )
  for id_, ifc in ifcs:
    i_conns += gen_ifc_conns( id_, id_, ifc )

  p_symbols.update( i_symbols )
  decls = p_decls + i_decls
  conns = p_conns + i_conns

  return p_symbols, decls, conns

#-------------------------------------------------------------------------
# gen_wire_decl_py
#-------------------------------------------------------------------------

def gen_wire_decl_py( name, _wire ):
  """Return the PyMTL definition of `wire`."""
  template = "s.mangled__{name} = {rhs}"
  rhs = "Wire( Bits{nbits} )"
  name = _verilator_name( name )
  if isinstance( _wire, rt.Array ):
    n_dim = _wire.get_dim_sizes()
    dtype = _wire.get_sub_type().get_dtype()
  else:
    n_dim = []
    dtype = _wire.get_dtype()
  nbits = dtype.get_length()
  for idx in reversed(n_dim):
    rhs = "[ " + rhs + ( " for _ in range({idx}) ]".format( **locals() ) )
  rhs = rhs.format( **locals() )
  return template.format( **locals() )

#-------------------------------------------------------------------------
# gen_comb_input
#-------------------------------------------------------------------------

def gen_comb_input( packed_ports ):
  def _gen_port_array_input( lhs, rhs, nbits, n_dim ):
    if not n_dim:
      return _gen_ref_write( lhs, rhs, nbits )
    else:
      ret = []
      for idx in range( n_dim[0] ):
        _lhs = lhs+"[{idx}]".format(**locals())
        _rhs = rhs+"[{idx}]".format(**locals())
        ret += _gen_port_array_input( _lhs, _rhs, nbits, n_dim[1:] )
      return ret
  ret = []
  for py_name, rtype in packed_ports:
    if _get_direction( rtype ) == 'InPort':
      if isinstance( rtype, rt.Array ):
        n_dim = rtype.get_dim_sizes()
        dtype = rtype.get_sub_type().get_dtype()
      else:
        n_dim = []
        dtype = rtype.get_dtype()
      v_name = _verilator_name( py_name )
      lhs = "_ffi_m."+v_name
      rhs = "s.mangled__"+v_name
      ret += _gen_port_array_input( lhs, rhs, dtype.get_length(), n_dim )
  return ret

#-------------------------------------------------------------------------
# gen_comb_output
#-------------------------------------------------------------------------

def gen_comb_output( packed_ports ):
  def _gen_port_array_output( lhs, rhs, nbits, n_dim ):
    if not n_dim:
      return _gen_ref_read( lhs, rhs, nbits )
    else:
      ret = []
      for idx in range( n_dim[0] ):
        _lhs = lhs+"[{idx}]".format(**locals())
        _rhs = rhs+"[{idx}]".format(**locals())
        ret += _gen_port_array_output( _lhs, _rhs, nbits, n_dim[1:] )
      return ret
  ret = []
  for py_name, rtype in packed_ports:
    if _get_direction( rtype ) == 'OutPort':
      if isinstance( rtype, rt.Array ):
        n_dim = rtype.get_dim_sizes()
        dtype = rtype.get_sub_type().get_dtype()
      else:
        n_dim = []
        dtype = rtype.get_dtype()
      v_name = _verilator_name( py_name )
      lhs = "s.mangled__" + v_name
      rhs = "_ffi_m." + v_name
      ret += _gen_port_array_output( lhs, rhs, dtype.get_length(), n_dim )
  return ret

#-------------------------------------------------------------------------
# gen_line_trace_py
#-------------------------------------------------------------------------

def gen_line_trace_py( packed_ports ):
  """Return the line trace method body that shows all interface ports."""
  ret = [ 'lt = ""' ]
  template = 'lt += "{my_name} = {{}}, ".format({full_name})'
  for name, port in packed_ports:
    my_name = name
    full_name = 's.mangled__'+_verilator_name(name)
    ret.append( template.format( **locals() ) )
  ret.append( 'return lt' )
  make_indent( ret, 2 )
  return '\n'.join( ret )

#-------------------------------------------------------------------------
# gen_internal_line_trace_py
#-------------------------------------------------------------------------

def gen_internal_line_trace_py( packed_ports ):
  """Return the line trace method body that shows all CFFI ports."""
  ret = [ '_ffi_m = s._ffi_m', 'lt = ""' ]
  template = \
    "lt += '{my_name} = {{}}, '.format(full_vector(s.mangled__{my_name}, _ffi_m.{my_name}))"
  for my_name, port in packed_ports:
    my_name = _verilator_name( my_name )
    ret.append( template.format(**locals()) )
  ret.append( 'return lt' )
  make_indent( ret, 2 )
  return '\n'.join( ret )
