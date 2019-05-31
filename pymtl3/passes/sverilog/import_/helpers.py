#=========================================================================
# helpers.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 30, 2019
"""Provide helper methods to the SystemVerilog import pass."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt

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

#-------------------------------------------------------------------------
# gen_all_ports
#-------------------------------------------------------------------------

def gen_all_ports( m, rtype ):
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

    def _is_of_port( rtype ):
      if isinstance(rtype, rt.Port):
        return True
      if isinstance(rtype, rt.Array) and isinstance(rtype.get_sub_type(), rt.Port):
        return True
      return False

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

def gen_signal_decl_py( name, port ):
  """Return the PyMTL definition of `port`."""
  nbits = port.get_dtype().get_length()
  direction = port.get_direction()
  if direction == 'input':
    port_type = 'InPort'
  elif direction == 'output':
    port_type = 'OutPort'
  else:
    assert False, "unrecognized port direction {}!".format( direction )
  return "s.{name} = {port_type}( Bits{nbits} )".format(**locals())

#-------------------------------------------------------------------------
# gen_comb_input
#-------------------------------------------------------------------------

def gen_comb_input( all_ports ):
  ret = []
  for py_name, port_rtype, _ in all_ports:
    if port_rtype.get_direction() == 'input':
      v_name = _verilator_name( py_name )
      nbits = port_rtype.get_dtype().get_length()
      ret += _gen_ref_write( "s._ffi_m."+v_name, "s."+py_name, nbits )
  return ret

#-------------------------------------------------------------------------
# gen_comb_output
#-------------------------------------------------------------------------

def gen_comb_output( all_ports ):
  # TODO: write only combinational outputs?
  ret = []
  for py_name, port_rtype, _ in all_ports:
    if port_rtype.get_direction() == 'output':
      v_name = _verilator_name( py_name )
      nbits = port_rtype.get_dtype().get_length()
      ret += _gen_ref_read( "s."+py_name, "s._ffi_m."+v_name, nbits )
  return ret

#-------------------------------------------------------------------------
# gen_seq_output
#-------------------------------------------------------------------------

def gen_seq_output( all_ports ):
  # TODO: write only sequential outputs?
  return gen_comb_output( all_ports )

#-------------------------------------------------------------------------
# gen_line_trace_py
#-------------------------------------------------------------------------

def gen_line_trace_py( all_ports ):
  """Return the line trace method body that shows all interface ports."""
  ret = [ 'lt = ""' ]
  template = 'lt += "{my_name} = {{}}, ".format({full_name})'
  for name, port, _ in all_ports:
    my_name = name
    full_name = 's.'+name
    ret.append( template.format( **locals() ) )
  ret.append( 'return lt' )
  make_indent( ret, 2 )
  return '\n'.join( ret )

#-------------------------------------------------------------------------
# gen_internal_line_trace_py
#-------------------------------------------------------------------------

def gen_internal_line_trace_py( ports ):
  """Return the line trace method body that shows all CFFI ports."""
  ret = [ 'lt = ""' ]
  template = "lt += '{my_name} = {{}}, '.format(s._ffi_m.{my_name}[{idx}])"
  for name, port, _ in ports:
    idx = 0
    my_name = name
    nbits = port.get_dtype().get_length()
    # if nbits <= 64:
      # ret.append( single_assign_template.format(**locals()) )
    # else:
    ret.append( template.format(**locals()) )
  ret.append( 'return lt' )
  make_indent( ret, 2 )
  return '\n'.join( ret )
