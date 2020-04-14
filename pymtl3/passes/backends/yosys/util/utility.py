#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Provide helper methods that might be useful to verilog passes."""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRGetter
from pymtl3.passes.rtlir import RTLIRType as rt

#-----------------------------------------------------------------------
# gen_packed_ports
#-----------------------------------------------------------------------

def get_rtype( _rtype ):
  if isinstance( _rtype, rt.Array ):
    n_dim = _rtype.get_dim_sizes()
    rtype = _rtype.get_sub_type()
  else:
    n_dim = []
    rtype = _rtype
  return n_dim, rtype

#-----------------------------------------------------------------------
# gen_mapped_ports
#-----------------------------------------------------------------------

def gen_mapped_ports( m, port_map, has_clk=True, has_reset=True, sep='__' ):
  """Return a list of (pname, vname, rt.Port/rt.Array ) that has all ports
  of `rtype`. This method performs SystemVerilog backend-specific name
  mangling and returns all ports that appear in the interface of component
  `rtype`. Each tuple contains a port or an array of port that has any data type
  allowed in RTLIRDataType.
  Shunning: Now we also take port_map into account. Two points to note:
  1. If a port's pname appears as a key in port_map, we need to use the
     corresponding value as vname
  2. For an n-D array of ports, we enforce the rule that assumes either no
     element is mapped in port_map, or _all_ of the elements are mapped.
  """

  port_map = {p._dsl._my_name:n for p, n in port_map.items()}

  def _mangle_vector( pname, vname, port, dtype, port_idx ):
    return [([pname], port_map[pname] if pname in port_map else vname,
             rt.Port(port.direction, dtype), port_idx)]

  def _mangle_struct( pname, vname, port, dtype, port_idx ):
    ret = []
    for field_name, field_dtype in dtype.get_all_properties().items():
      ret += _mangle_dtype(f"{pname}.{field_name}", f"{vname}{sep}{field_name}",
                           port, field_dtype, port_idx)
    return ret

  def _mangle_packed( pname, vname, port, dtype, n_dim, port_idx ):
    if not n_dim:
      return _mangle_dtype( pname, vname, port, dtype, port_idx )
    else:
      ret = []
      for i in range(n_dim[0]):
        ret += _mangle_packed( f"{pname}[{i}]", f"{vname}{sep}{i}", port, dtype, n_dim[1:], port_idx )
      return ret

  def _mangle_dtype( pname, vname, port, dtype, port_idx ):
    if isinstance(dtype, rdt.Vector):
      return _mangle_vector(pname, vname, port, dtype, port_idx)
    elif isinstance(dtype, rdt.Struct):
      return _mangle_struct(pname, vname, port, dtype, port_idx)
    elif isinstance(dtype, rdt.PackedArray):
      return _mangle_packed(pname, vname, port,
                            dtype.get_sub_dtype(), dtype.get_dim_sizes(), port_idx)
    else:
      assert False, f'unrecognized data type {dtype}!'

  def _mangle_port( pname, vname, port, n_dim, port_idx ):
    # Normal port
    if not n_dim:
      return _mangle_dtype( pname, vname, port, port.get_dtype(), port_idx )

    # Handle port array. We just assume if one element of the port array
    # is mapped, we need the user to map every element in the array.
    else:
      ret = []
      for i in range(n_dim[0]):
        ret += _mangle_port(f"{pname}[{i}]", f"{vname}{sep}{i}", port, n_dim[1:], port_idx)
      return ret

  def _mangle_ifc( pname, vname, ifc, n_dim, port_idx ):
    ret = []
    if not n_dim:
      for port_name, port_rtype in ifc.get_all_properties_packed():
        port_n_dim, port_rtype = get_rtype( port_rtype )
        if isinstance(port_rtype, rt.InterfaceView):
          ret += _mangle_ifc(f"{pname}.{port_name}", f"{vname}{sep}{port_name}",
                              port_rtype, port_n_dim, port_idx)
        elif isinstance(port_rtype, rt.Port):
          ret += _mangle_port(f"{pname}.{port_name}", f"{vname}{sep}{port_name}",
                              port_rtype, port_n_dim, port_idx)
        else:
          assert False, "unrecognized interface/port {port_rtype}!"
    else:
      for i in range(n_dim[0]):
        ret += _mangle_ifc(f"{pname}[{i}]", f"{vname}{sep}{i}", ifc, n_dim[1:], port_idx+1)
    return ret

  # We start from all packed ports/interfaces, and unpack arrays if
  # it is found in a port.
  rtype = RTLIRGetter(cache=False).get_component_ifc_rtlir(m)
  ret = []

  for name, port in rtype.get_ports_packed():
    if not has_clk and name == 'clk':      continue
    if not has_reset and name == 'reset':  continue
    p_n_dim, p_rtype = get_rtype( port )
    ret += _mangle_port( name, name, p_rtype, p_n_dim, 0 )

  for name, ifc in rtype.get_ifc_views_packed():
    i_n_dim, i_rtype = get_rtype( ifc )
    ret += _mangle_ifc( name, name, i_rtype, i_n_dim, 0 )

  return ret
