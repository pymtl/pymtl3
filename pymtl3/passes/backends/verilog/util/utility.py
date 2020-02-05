#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Provide helper methods that might be useful to verilog passes."""

import copy
import os
import shutil
import textwrap
from hashlib import blake2b

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.rtlir.util.utility import get_component_full_name


def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '
  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

def get_component_unique_name( c_rtype ):
  full_name = get_component_full_name( c_rtype )

  if len( full_name ) < 64:
    return full_name

  comp_name = c_rtype.get_name()
  param_hash = blake2b(digest_size = 8)
  param_hash.update(full_name[len(comp_name):].encode('ascii'))
  param_name = param_hash.hexdigest()
  return comp_name + "__" + param_name

  def get_string( obj ):
    """Return the string that identifies `obj`"""
    if isinstance(obj, type): return obj.__name__
    return str( obj )

def wrap( s ):
  col = shutil.get_terminal_size().columns
  return "\n".join(sum((textwrap.wrap(line, col) for line in s.split("\n")), []))

def expand( v ):
  return os.path.expanduser(os.path.expandvars(v))

def get_dir( cur_file ):
  return os.path.dirname(os.path.abspath(cur_file))+os.path.sep

def get_file_hash( file_path ):
  with open( file_path, 'r' ) as fd:
    hash_inst = blake2b()
    string = ''.join( fd.readlines() ).encode( 'ascii' )
    hash_inst.update(string)
    return hash_inst.hexdigest()

verilog_keyword = [
  # Verilog-1995 reserved keywords
  "always", "and", "assign", "begin", "buf", "bufif0", "bufif1", "case",
  "casex", "casez", "cmos", "deassign", "default", "defparam", "disable",
  "edge", "else", "end", "endcase", "endmodule", "endfunction", "endprimitive",
  "endspecify", "endtable", "endtask", "event", "for", "force", "forever",
  "fork", "function", "highz0", "highz1", "if", "ifnone", "initial",
  "inout", "input", "output", "integer", "join", "large", "macromodule",
  "medium", "module", "nand", "negedge", "nmos", "nor", "not", "notif0",
  "notif1", "or", "output", "parameter", "pmos", "posedge", "primitive",
  "pull0", "pull1", "pullup", "pulldown", "rcmos", "real", "realtime",
  "reg", "release", "repeat", "rnmos", "rpmos", "rtran", "rtranif0",
  "rtranif1", "scalared", "small", "specify", "specparam", "strong0",
  "strong1", "supply0", "supply1", "table", "task", "time", "tran",
  "tranif0", "tranif1", "tri", "tri0", "tri1", "triand", "trior",
  "trireg", "vectored", "wait", "wand", "weak0", "weak1", "while",
  "wire", "wor", "xnor", "xor",
  # Verilog-2001 reserved keywords
  "automatic", "cell", "config", "design", "endconfig", "endgenerate",
  "generate", "genvar", "incdir", "include", "instance", "liblist",
  "library", "localparam", "noshowcancelled", "pulsestyle_onevent",
  "pulsestyle_ondetect", "showcancelled", "signed", "unsigned", "use",
  # Verilog-2005 reserved keywords
  "uwire",
  # SystemVerilog-2005 reserved keywords
  "alias", "always_comb", "always_ff", "always_latch", "assert", "assume",
  "before", "bind", "bins", "binsof", "bit", "break", "byte", "chandle",
  "class", "clocking", "const", "constraint", "context", "continue",
  "cover", "covergroup", "coverpoint", "cross", "dist", "do", "endclass",
  "endclocking", "endgroup", "endinterface", "endpackage", "endprimitive",
  "endprogram", "endproperty", "endsequence", "enum", "expect", "export",
  "extends", "extern", "final", "first_match", "foreach", "forkjoin",
  "iff", "ignore_bins", "illegal_bins", "import", "inside", "int", "interface",
  "intersect", "join_any", "join_none", "local", "logic", "longint", "matches",
  "modport", "new", "null", "package", "packed", "priority", "program",
  "property", "protected", "pure", "rand", "randc", "randcase", "randsequence",
  "ref", "return", "sequence", "shortint", "shortreal", "solve", "static",
  "string", "struct", "super", "tagged", "this", "throughout", "timeprecision",
  "timeunit", "type", "typedef", "union", "unique", "var", "virtual", "void",
  "wait_order", "wildcard", "with", "within"
]

verilog_reserved = set( verilog_keyword )

#-----------------------------------------------------------------------
# gen_packed_ports
#-----------------------------------------------------------------------

def _get_rtype( _rtype ):
  if isinstance( _rtype, rt.Array ):
    n_dim = _rtype.get_dim_sizes()
    rtype = _rtype.get_sub_type()
  else:
    n_dim = []
    rtype = _rtype
  return n_dim, rtype

def _mangle_port( id_, port, n_dim ):
  if not n_dim:
    return [ ( id_, port ) ]
  else:
    return [ ( id_, rt.Array( n_dim, port ) ) ]

def _mangle_interface( id_, ifc, n_dim ):
  if not n_dim:
    ret = []
    all_properties = ifc.get_all_properties_packed()
    for name, rtype in all_properties:
      _n_dim, _rtype = _get_rtype( rtype )
      if isinstance( _rtype, rt.Port ):
        ret += _mangle_port( id_+"__"+name, _rtype, _n_dim )
      elif isinstance( _rtype, rt.InterfaceView ):
        ret += _mangle_interface( id_+"__"+name, _rtype, _n_dim )
      else:
        assert False, f"{name} is not interface(s) or port(s)!"
  else:
    ret = []
    for i in range( n_dim[0] ):
      ret += _mangle_interface( id_+"__"+str(i), ifc, n_dim[1:] )
  return ret

def gen_packed_ports( irepr ):
  """Return a list of (name, rt.Port) that has all ports of `irepr`.

  This method performs SystemVerilog backend-specific name mangling and
  returns all ports that appear in the interface of component `irepr`.
  Each tuple contains a port or an array of port that has any data type
  allowed in RTLIRDataType.
  """
  packed_ports = []
  ports = irepr.get_ports_packed()
  ifcs = irepr.get_ifc_views_packed()
  for id_, port in ports:
    p_n_dim, p_rtype = _get_rtype( port )
    packed_ports += _mangle_port( id_, p_rtype, p_n_dim )
  for id_, ifc in ifcs:
    i_n_dim, i_rtype = _get_rtype( ifc )
    packed_ports += _mangle_interface( id_, i_rtype, i_n_dim )
  return packed_ports

def gen_unpacked_ports( irepr ):
  """Return a list of (name, rt.Port) that has all ports of `irepr`.

  This method performs SystemVerilog backend-specific name mangling and
  returns all ports that appear in the interface of component `irepr`.
  Each tuple contains a port or an array of port that has any data type
  allowed in RTLIRDataType.
  """
  unpacked_ports = []
  ports = irepr.get_ports()
  ifcs = irepr.get_ifc_views()
  for id_, port in ports:
    p_n_dim, p_rtype = _get_rtype( port )
    unpacked_ports += _mangle_port( id_, p_rtype, p_n_dim )
  for id_, ifc in ifcs:
    i_n_dim, i_rtype = _get_rtype( ifc )
    unpacked_ports += _mangle_interface( id_, i_rtype, i_n_dim )
  return unpacked_ports

#-----------------------------------------------------------------------
# gen_mapped_packed_ports
#-----------------------------------------------------------------------

def gen_mapped_packed_ports(
    m, _p_map, has_clk = True, has_reset = True, packed_to_unpacked = False ):

  is_packed_to_unpacked = packed_to_unpacked and ( '[' in ''.join(list(_p_map.keys())) )

  # Create a new _p_map based on Verilog name mangling rules
  new_pmap = {}
  for name, v_name in _p_map.items():
    new_pmap[name.replace('.', '__')] = v_name
  _p_map = new_pmap

  def _array_port_mangle( name, alias, port, n_dim ):
    if not n_dim:
      return [ ( name, alias, port ) ]
    else:
      ret = []
      for i in range(n_dim[0]):
        ret += _array_port_mangle( f'{name}__{i}', f'{name}[{i}]', port, n_dim[1:] )
      return ret

  irepr = get_component_ifc_rtlir( m )
  no_clk, no_reset = not has_clk, not has_reset
  p_map = lambda k: _p_map[k] if k in _p_map else k
  _packed_ports = gen_packed_ports( irepr )

  clk   = next(filter(lambda x: x[0] == 'clk',   _packed_ports))[1]
  reset = next(filter(lambda x: x[0] == 'reset', _packed_ports))[1]

  if not is_packed_to_unpacked:
    packed_ports = \
        ([('clk', '' if no_clk else p_map('clk'), clk)] if no_clk else []) + \
        ([('reset', '' if no_reset else p_map('reset'), reset)] if no_reset else []) + \
        [ (n, p_map(n), p) for n, p in _packed_ports \
          if not (n == 'clk' and no_clk or n == 'reset' and no_reset)]

    return packed_ports

  else:
    packed_ports = \
      ([('clk', '' if no_clk else p_map('clk'), clk)] if no_clk else []) + \
      ([('reset', '' if no_reset else p_map('reset'), reset)] if no_reset else [])

    array_ports_to_be_mapped = \
        { name.split('[')[0] for name in _p_map.keys() if '[' in name }

    for name, port in _packed_ports:
      use_orig = True
      if not (name == 'clk' and no_clk or name == 'reset' and no_reset):
        # If this is an array of ports and will be mapped to different names
        if isinstance(port, rt.Array) and name in array_ports_to_be_mapped:
          use_orig = False
          unpacked_ports = \
              _array_port_mangle( name, name, port.get_sub_type(), port.get_dim_sizes() )
          for unpacked_name, unpacked_alias, unpacked_port in unpacked_ports:
            assert unpacked_alias in _p_map, \
                f"You must provide a name for all ports in {name} through port_map!"
            packed_ports.append(
                ( unpacked_name, p_map( unpacked_alias ), unpacked_port ) )
      if use_orig:
        packed_ports.append(( name, p_map(name), port ))
    return packed_ports

#-----------------------------------------------------------------------
# gen_mapped_unpacked_ports
#-----------------------------------------------------------------------

def gen_mapped_unpacked_ports( m, _p_map, has_clk = True, has_reset = True ):
  # Create a new _p_map based on Verilog name mangling rules
  new_pmap = {}
  for name, v_name in _p_map.items():
    new_pmap[name.replace('.', '__')] = v_name
  _p_map = new_pmap

  irepr = get_component_ifc_rtlir( m )
  no_clk, no_reset = not has_clk, not has_reset
  p_map = lambda k: _p_map[k] if k in _p_map else k

  _unpacked_ports = gen_unpacked_ports( irepr )
  clk   = next(filter(lambda x: x[0] == 'clk',   _unpacked_ports))[1]
  reset = next(filter(lambda x: x[0] == 'reset', _unpacked_ports))[1]

  unpacked_ports = \
      ([('clk', '' if no_clk else p_map('clk'), clk)] if no_clk else []) + \
      ([('reset', '' if no_reset else p_map('reset'), reset)] if no_reset else []) + \
      [ (n, p_map(n), p) for n, p in _unpacked_ports \
        if not (n == 'clk' and no_clk or n == 'reset' and no_reset)]

  return unpacked_ports
