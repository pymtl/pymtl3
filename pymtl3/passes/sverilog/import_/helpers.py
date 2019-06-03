#=========================================================================
# helpers.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 30, 2019
"""Provide helper methods to the SystemVerilog import pass."""

from __future__ import absolute_import, division, print_function

import copy

from pymtl3.datatypes import Bits, mk_bits
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.utility import make_indent

#-------------------------------------------------------------------------
# Internal helper methods
#-------------------------------------------------------------------------

def _verilator_name( name ):
  return name.replace('__', '___05F').replace('$', '__024')

def _gen_ref_write( lhs, rhs, nbits ):
  if nbits <= 64:
    return [ "{lhs}[0] = int({rhs})".format( **locals() ) ]
  else:
    ret = []
    ITEM_BITWIDTH = 32
    num_assigns = (nbits-1)/ITEM_BITWIDTH+1
    for idx in xrange(num_assigns):
      l = ITEM_BITWIDTH*idx
      r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
      ret.append("{lhs}[{idx}] = int({rhs}[{l}:{r}])".format(**locals()))
    return ret

def _gen_ref_read( lhs, rhs, nbits ):
  if nbits <= 64:
    return [ "{lhs} = {rhs}[0]".format( **locals() ) ]
  else:
    ret = []
    ITEM_BITWIDTH = 32
    num_assigns = (nbits-1)/ITEM_BITWIDTH+1
    for idx in xrange(num_assigns):
      l = ITEM_BITWIDTH*idx
      r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
      ret.append("{lhs}[{l}:{r}] = {rhs}[{idx}]".format(**locals()))
    return ret

def _is_of_port( rtype ):
  if isinstance(rtype, rt.Port):
    return True
  if isinstance(rtype, rt.Array) and isinstance(rtype.get_sub_type(), rt.Port):
    return True
  return False

#-------------------------------------------------------------------------
# gen_all_ports
#-------------------------------------------------------------------------

def gen_all_ports( rtype ):
  """Return a list of (name, rt.Port, obj) that has all ports of `rtype`.
  
  This method performs SystemVerilog backend-specific name mangling and
  returns all ports that appear in the interface of component `rtype`.
  Each tuple contains a single port that has data type of rdt.Vector ( that
  is, every struct field will also be name-mangeld ).
  """
  def _mangle_dtype( id_, direc, dtype ):

    def _gen_packed_array( id_, direc, dtype, n_dim, c_n_dim ):
      if not n_dim:
        return _mangle_dtype( id_+c_n_dim, direc, dtype )
      else:
        ret = []
        for idx in xrange(n_dim[0]):
          ret += _gen_packed_array(
              id_, direc, dtype, n_dim[1:], c_n_dim+'_$'+str(idx) )
        return ret

    if isinstance( dtype, rdt.Vector ):
      return [ ( id_, rt.Port( direc, dtype ) ) ]

    elif isinstance( dtype, rdt.Struct ):
      ret = []
      all_properties = dtype.get_all_properties()
      for field_id, field_dtype in all_properties:
        ret += _mangle_dtype( id_+'_$'+field_id, direc, field_dtype )
      return ret

    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return _gen_packed_array( id_, direc, sub_dtype, n_dim, "" )

    else:
      assert False, "unrecognized data type {}".format( dtype )

  def _mangle_port( id_, _port ):

    def _gen_port( id_, direc, dtype, n_dim, c_n_dim ):
      if not n_dim:
        return _mangle_dtype( id_+c_n_dim, direc, dtype )
      else:
        ret = []
        for idx in xrange(n_dim[0]):
          ret += _gen_port(id_, direc, dtype, n_dim[1:], c_n_dim+'_$'+str(idx))
        return ret

    if isinstance( _port, rt.Array ):
      port = _port.get_sub_type()
      n_dim = _port.get_dim_sizes()
    else:
      assert isinstance( _port, rt.Port )
      port = _port
      n_dim = []
    direction = port.get_direction()
    dtype = port.get_dtype()
    return _gen_port(id_, direction, dtype, n_dim, '')

  def _mangle_interface( id_, _ifc ):

    def _gen_single_ifc( id_, ifc ):
      ret = []
      all_properties = ifc.get_all_properties_packed()
      for prop_name, prop_rtype in all_properties:
        if _is_of_port( prop_rtype ):
          ret += _mangle_port( id_+'_$'+prop_name, prop_rtype )
        else:
          ret += _flatten_ifc( id_+'_$'+prop_name, prop_rtype )
      return ret

    def _gen_ifc( id_, ifc, n_dim, c_n_dim ):
      if not n_dim:
        return _gen_single_ifc( id_+c_n_dim, ifc )
      else:
        ret = []
        for idx in xrange(n_dim[0]):
          ret += _gen_ifc( id_, ifc, n_dim[1:], c_n_dim+'_$'+str(idx) )
        return ret

    def _flatten_ifc( id_, _ifc ):
      if isinstance( _ifc, rt.Array ):
        ifc = _ifc.get_sub_type()
        n_dim = _ifc.get_dim_sizes()
      else:
        ifc = _ifc
        n_dim = []
      return _gen_ifc( id_, ifc, n_dim, "" )

    return _flatten_ifc( id_, _ifc )

  all_ports = []
  ports = rtype.get_ports_packed()
  ifcs = rtype.get_ifc_views_packed()
  for id_, port in ports:
    all_ports += _mangle_port( id_, port )
  for id_, ifc in ifcs:
    all_ports += _mangle_interface( id_, ifc )
  return all_ports

#-------------------------------------------------------------------------
# gen_signal_decl_c
#-------------------------------------------------------------------------

def gen_signal_decl_c( name, port ):
  """Return C variable declaration of `port`."""
  nbits = port.get_dtype().get_length()
  if    nbits <= 8:  data_type = 'unsigned char'
  elif  nbits <= 16: data_type = 'unsigned short'
  elif  nbits <= 32: data_type = 'unsigned int'
  elif  nbits <= 64: data_type = 'unsigned long'
  else:              data_type = 'unsigned int'
  name = _verilator_name( name )
  return '{data_type} * {name};'.format( **locals() )

#-------------------------------------------------------------------------
# gen_signal_init_c
#-------------------------------------------------------------------------

def gen_signal_init_c( name, port ):
  """Return C port variable initialization."""
  nbits     = port.get_dtype().get_length()
  deference = '&' if nbits <= 64 else ''
  name      = _verilator_name( name )
  return 'm->{name} = {deference}model->{name};'.format( **locals() )

#-------------------------------------------------------------------------
# gen_signal_decl_py
#-------------------------------------------------------------------------

def gen_signal_decl_py( rtype ):
  """Return the PyMTL definition of all interface ports of `rtype`."""

  def _get_direction( port ):
    d = port.get_direction()
    if d == 'input':
      return 'InPort'
    elif d == 'output':
      return 'OutPort'
    else:
      assert False, "unrecognized direction {}!".format( d )

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
      if isinstance( _port, rt.Array ):
        n_dim = _port.get_dim_sizes()
        rhs = "{direction}( {dtype} )"
        port = _port.get_sub_type()
        _n_dim = copy.copy( n_dim )
        _n_dim.reverse()
        for length in _n_dim:
          rhs = "[ " + rhs + (" for _ in xrange({length}) ]".format(**locals()))
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

      def _get_arg_str( obj ):
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
        elif isinstance( obj, type ) and issubclass( obj, Bits ):
          nbits = obj.nbits
          Bits_name = "Bits{nbits}".format( **locals() )
          if Bits_name not in symbols and nbits >= 256:
            Bits_class = mk_bits( nbits )
            symbols.update( { Bits_name : Bits_class } )
          return Bits_name
        else:
          assert False, \
            "Interface constructor argument {} is not an integer or Bits!". \
              format( obj )

      name, cls = ifc.get_name(), ifc.get_class()
      if name not in symbols:
        symbols.update( { name : cls } )
      arg_list = []
      args = ifc.get_args()
      for obj in args[0]:
        arg_list.append( _get_arg_str( obj ) )
      for arg_name, arg_obj in args[1].iteritems():
        arg_list.append( arg_name + " = " + _get_arg_str( arg_obj ) )
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
          rhs = "[ " + rhs + (" for _ in xrange({length}) ]".format(**locals()))
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

  def gen_packed_array_conns( id_py, id_v, dtype, n_dim, py, v ):
    if not n_dim:
      return gen_dtype_conns( id_py+py, id_v+v, dtype )
    else:
      ret = []
      for idx in xrange(n_dim[0]):
        _py = py + "[{idx}]".format( **locals() )
        _v = v + "_${idx}".format( **locals() )
        ret += \
            gen_packed_array_conns( id_py, id_v, dtype, n_dim[1:], _py, _v )
      return ret

  def gen_dtype_conns( id_py, id_v, dtype ):
    template = "s.connect( {py}, {v} )"
    if isinstance( dtype, rdt.Vector ):
      py, v = "s."+id_py, "s.mangled__"+id_v
      return [ template.format( **locals() ) ]
    elif isinstance( dtype, rdt.Struct ):
      ret = []
      all_properties = dtype.get_all_properties()
      for field_id, field_dtype in all_properties:
        py = id_py + ".{field_id}".format( **locals() )
        v = id_v + "_${field_id}".format( **locals() )
        ret += gen_dtype_conns( py, v, field_dtype )
      return ret
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return gen_packed_array_conns( id_py, id_v, sub_dtype, n_dim, "", "" )
    else:
      assert False, "unrecognized data type {}!".format( dtype )

  def gen_port_conns( id_py, id_v, _port ):

    def _gen_port_conns( id_py, id_v, port, n_dim, py, v ):
      if not n_dim:
        dtype = port.get_dtype()
        return gen_dtype_conns( id_py+py, id_v+v, dtype )
      else:
        ret = []
        for idx in xrange(n_dim[0]):
          _py = py + "[{idx}]".format( **locals() )
          _v = v + "_${idx}".format( **locals() )
          ret += _gen_port_conns( id_py, id_v, port, n_dim[1:], _py, _v )
        return ret

    if isinstance( _port, rt.Array ):
      n_dim = _port.get_dim_sizes()
      port = _port.get_sub_type()
    else:
      n_dim = []
      port = _port
    return _gen_port_conns( id_py, id_v, port, n_dim, "", "" )

  def gen_ifc_conns( id_py, id_v, _ifc ):

    def _gen_single_ifc_conn( id_py, id_v, ifc ):
      ret = []
      all_properties = ifc.get_all_properties_packed()
      for prop_name, prop_rtype in all_properties:
        _id_py = id_py + ".{prop_name}".format( **locals() )
        _id_v = id_v + "_${prop_name}".format( **locals() )
        if _is_of_port( prop_rtype ):
          ret += gen_port_conns( _id_py, _id_v, prop_rtype )
        else:
          ret += gen_ifc_conns( _id_py, _id_v, prop_rtype )
      return ret

    def _gen_ifc_conns( id_py, id_v, ifc, n_dim, py, v ):
      if not n_dim:
        return _gen_single_ifc_conn( id_py+py, id_v+v, ifc )
      else:
        ret = []
        for idx in xrange( n_dim[0] ):
          _py = py + "[{idx}]".format( **locals() )
          _v = v + "_${idx}".format( **locals() )
          ret += _gen_ifc_conns( id_py, id_v, ifc, n_dim[1:], _py, _v )
        return ret

    if isinstance( _ifc, rt.Array ):
      n_dim = _ifc.get_dim_sizes()
      ifc = _ifc.get_sub_type()
    else:
      n_dim = []
      ifc = _ifc
    return _gen_ifc_conns( id_py, id_v, ifc, n_dim, "", "" )

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

def gen_wire_decl_py( name, wire ):
  """Return the PyMTL definition of `wire`."""
  nbits = wire.get_dtype().get_length()
  return "s.mangled__{name} = Wire( Bits{nbits} )".format(**locals())

#-------------------------------------------------------------------------
# gen_comb_input
#-------------------------------------------------------------------------

def gen_comb_input( all_ports ):
  ret = []
  for py_name, port_rtype in all_ports:
    if port_rtype.get_direction() == 'input':
      v_name = _verilator_name( py_name )
      nbits = port_rtype.get_dtype().get_length()
      ret += _gen_ref_write( "s._ffi_m."+v_name, "s.mangled__"+py_name, nbits )
  return ret

#-------------------------------------------------------------------------
# gen_comb_output
#-------------------------------------------------------------------------

def gen_comb_output( all_ports ):
  ret = []
  for py_name, port_rtype in all_ports:
    if port_rtype.get_direction() == 'output':
      v_name = _verilator_name( py_name )
      nbits = port_rtype.get_dtype().get_length()
      ret += _gen_ref_read( "s.mangled__"+py_name, "s._ffi_m."+v_name, nbits )
  return ret

#-------------------------------------------------------------------------
# gen_constraints
#-------------------------------------------------------------------------

def gen_constraints( all_ports ):
  ret = []
  template = "U( seq_upblk ) < {op}( {signal_name} ),"
  for py_name, port_rtype in all_ports:
    direction = port_rtype.get_direction()
    signal_name = "s.mangled__" + py_name
    if direction == 'input':
      op = 'WR'
    elif direction == 'output':
      op = 'RD'
    else:
      assert False, "unrecognized port direction {}".format( direction )
    ret.append( template.format( **locals() ) )
  return ret


#-------------------------------------------------------------------------
# gen_line_trace_py
#-------------------------------------------------------------------------

def gen_line_trace_py( all_ports ):
  """Return the line trace method body that shows all interface ports."""
  ret = [ 'lt = ""' ]
  template = 'lt += "{my_name} = {{}}, ".format({full_name})'
  for name, port in all_ports:
    my_name = name
    full_name = 's.mangled__'+name
    ret.append( template.format( **locals() ) )
  ret.append( 'return lt' )
  make_indent( ret, 2 )
  return '\n'.join( ret )

#-------------------------------------------------------------------------
# gen_internal_line_trace_py
#-------------------------------------------------------------------------

def gen_internal_line_trace_py( all_ports ):
  """Return the line trace method body that shows all CFFI ports."""
  ret = [ 'lt = ""' ]
  template = \
    "lt += '{my_name} = {{}}, '.format(full_vector(s._ffi_m.{my_name}))"
  for my_name, port in all_ports:
    ret.append( template.format(**locals()) )
  ret.append( 'return lt' )
  make_indent( ret, 2 )
  return '\n'.join( ret )
