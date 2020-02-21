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

def get_rtype( _rtype ):
  if isinstance( _rtype, rt.Array ):
    n_dim = _rtype.get_dim_sizes()
    rtype = _rtype.get_sub_type()
  else:
    n_dim = []
    rtype = _rtype
  return n_dim, rtype

def _mangle_port( pname, vname, port, n_dim ):
  if not n_dim:
    return [ ( pname, vname, port ) ]
  else:
    return [ ( pname, vname, rt.Array( n_dim, port ) ) ]

def _mangle_ifc( pname, vname, ifc, n_dim ):
  if not n_dim:
    ret = []
    all_properties = ifc.get_all_properties_packed()
    for name, rtype in all_properties:
      _n_dim, _rtype = get_rtype( rtype )
      if isinstance( _rtype, rt.Port ):
        ret += _mangle_port( f"{pname}.{name}", f"{vname}__{name}", _rtype, _n_dim )
      elif isinstance( _rtype, rt.InterfaceView ):
        ret += _mangle_ifc(  f"{pname}.{name}", f"{vname}__{name}", _rtype, _n_dim )
      else:
        assert False, f"{name} is not interface(s) or port(s)!"
  else:
    ret = []
    for i in range( n_dim[0] ):
      ret += _mangle_ifc( f"{pname}[{i}]", f"{vname}__{i}", ifc, n_dim[1:] )
  return ret

def gen_packed_ports( rtype ):
  """Return a list of (name, rt.Port ) that has all ports of `rtype`.
  This method performs SystemVerilog backend-specific name mangling and
  returns all ports that appear in the interface of component `rtype`.
  Each tuple contains a port or an array of port that has any data type
  allowed in RTLIRDataType.
  """
  packed_ports = []
  ports = rtype.get_ports_packed()
  ifcs = rtype.get_ifc_views_packed()
  for name, port in ports:
    p_n_dim, p_rtype = get_rtype( port )
    packed_ports += _mangle_port( name, name, p_rtype, p_n_dim )
  for name, ifc in ifcs:
    i_n_dim, i_rtype = get_rtype( ifc )
    packed_ports += _mangle_ifc( name, name, i_rtype, i_n_dim )
  return packed_ports

#-----------------------------------------------------------------------
# gen_mapped_packed_ports
#-----------------------------------------------------------------------

def gen_mapped_packed_ports( m, p_map, has_clk = True, has_reset = True ):
  # Create name-based port map
  _packed_ports = gen_packed_ports( get_component_ifc_rtlir(m) )

  packed_ports = []
  for pname, vname, port in _packed_ports:
    if not has_clk and pname == 'clk':      continue
    if not has_reset and pname == 'reset':  continue
    print('x'*100, pname)
    if pname in p_map:
      packed_ports.append( (pname, p_map[pname], port) )
    else:
      packed_ports.append( (pname, vname, port) )
  return packed_ports
