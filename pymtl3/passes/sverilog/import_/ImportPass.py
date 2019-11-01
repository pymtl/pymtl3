#=========================================================================
# ImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 25, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""

import copy
import importlib
import linecache
import os
import shutil
import subprocess
import sys
from textwrap import indent

from pymtl3.datatypes import Bits, is_bitstruct_class, is_bitstruct_inst, mk_bits
from pymtl3.dsl import Component
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.sverilog.errors import SVerilogImportError
from pymtl3.passes.sverilog.util.utility import (
    expand,
    get_component_unique_name,
    make_indent,
    wrap,
)

from .ImportConfigs import ImportConfigs

try:
  # Python 2
  reload
except NameError:
  # Python 3
  from importlib import reload

class ImportPass( BasePass ):
  """Import an arbitrary SystemVerilog module as a PyMTL component.

  The import pass takes as input a PyMTL component hierarchy where
  the components to be imported have an `import` entry in their parameter
  dictionary( set by calling the `set_parameter` PyMTL API ).
  This pass assumes the modules to be imported are located in the current
  directory and have name {full_name}.sv where `full_name` is the name of
  component's class concatanated with the list of arguments of its construct
  method. It has the following format:
      > {module_name}[__{parameter_name}_{parameter_value}]*
  As an example, component mux created through `mux = Mux(Bits32, 2)` has a
  full name `Mux__Type_Bits32__ninputs_2`.
  The top module inside the target .sv file should also have a full name.
  """
  def __call__( s, top ):
    s.top = top
    if not top._dsl.constructed:
      raise SVerilogImportError( top,
        f"please elaborate design {top} before applying the import pass!" )
    ret = s.traverse_hierarchy( top )
    if ret is None:
      ret = top
    return ret

  def traverse_hierarchy( s, m ):
    if hasattr(m, f"{s.get_backend_name()}_import") and \
       isinstance(s.get_config(m), ImportConfigs) and \
       s.get_config(m).is_import_enabled():
      s.get_config(m).fill_missing( m )
      return s.do_import( m )
    else:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

  def do_import( s, m ):
    try:
      imp = s.get_imported_object( m )
      if m is s.top:
        return imp
      else:
        s.top.replace_component_with_obj( m, imp )
    except AssertionError as e:
      msg = '' if e.args[0] is None else e.args[0]
      raise SVerilogImportError( m, msg )

  #-----------------------------------------------------------------------
  # Backend-specific methods
  #-----------------------------------------------------------------------

  def get_backend_name( s ):
    return "sverilog"

  def get_config( s, m ):
    return m.sverilog_import

  def get_translation_namespace( s, m ):
    return m._pass_sverilog_translation

  #-----------------------------------------------------------------------
  # is_cached
  #-----------------------------------------------------------------------

  def is_cached( s, m, full_name ):
    cached = False

    # Only components translated by pymtl translation passes will be cached
    try:
      is_same = s.get_translation_namespace(m).is_same
    except AttributeError:
      is_same = False

    # Check if the verilated model is cached
    cached = False
    obj_dir = 'obj_dir_' + full_name
    c_wrapper = full_name + '_v.cpp'
    py_wrapper = full_name + '_v.py'
    shared_lib = f'lib{full_name}_v.so'
    if is_same and os.path.exists(obj_dir) and os.path.exists(c_wrapper) and \
       os.path.exists(py_wrapper) and os.path.exists(shared_lib):
      cached = True

    return cached

  #-----------------------------------------------------------------------
  # get_imported_object
  #-----------------------------------------------------------------------

  def get_imported_object( s, m ):
    config = s.get_config( m )
    rtype = get_component_ifc_rtlir( m )
    full_name = get_component_unique_name( rtype )
    p_map = config.get_port_map() if config.is_port_mapped() else lambda x: x
    no_clk, no_reset = not config.has_clk(), not config.has_reset()
    _packed_ports = s.gen_packed_ports( rtype )
    clk = next(filter(lambda x: x[0]=='clk', _packed_ports))[1]
    reset = next(filter(lambda x: x[0]=='reset', _packed_ports))[1]
    packed_ports = \
        ([('clk', '' if no_clk else p_map('clk'), clk)] if no_clk else []) + \
        ([('reset', '' if no_reset else p_map('reset'), reset)] if no_reset else []) + \
        [ (n, p_map(n), p) for n, p in _packed_ports \
          if not (n == 'clk' and no_clk or n == 'reset' and no_reset)]

    cached = s.is_cached( m, full_name )

    # Create a new Verilog source file if a new top-level wrapper is needed
    if config.is_top_wrapper():
      s.add_param_wrapper( m, config, rtype, packed_ports )

    s.create_verilator_model( m, config, cached )

    port_cdefs = \
        s.create_verilator_c_wrapper( m, config, packed_ports, cached )

    s.create_shared_lib( m, config, cached )

    symbols = \
        s.create_py_wrapper( m, config, rtype, packed_ports, port_cdefs, cached )

    imp = s.import_component( m, config, symbols )

    return imp

  #-----------------------------------------------------------------------
  # create_verilator_model
  #-----------------------------------------------------------------------

  def create_verilator_model( s, m, config, cached ):
    """Verilate module `m`."""
    config.check_options()
    config.vprint("\n=====Verilate model=====")
    if not cached:
      # Generate verilator command
      cmd = config.create_vl_cmd()

      # Remove obj_dir directory if it already exists.
      # obj_dir is where the verilator output ( C headers and sources ) is stored
      obj_dir = config.get_vl_mk_dir()
      if os.path.exists( obj_dir ):
        shutil.rmtree( obj_dir )

      # Try to call verilator
      try:
        config.vprint(f"Verilating {config.get_top_module()} with command:", 2)
        config.vprint(f"{cmd}", 4)
        subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True )
      except subprocess.CalledProcessError as e:
        err_msg = e.output if not isinstance(e.output, bytes) else \
                  e.output.decode('utf-8')
        import_err_msg = \
            f"Fail to verilate model {config.get_option('top_module')}\n"\
            f"  Verilator command:\n{indent(cmd, '  ')}\n\n"\
            f"  Verilator output:\n{indent(wrap(err_msg), '  ')}\n"
        raise SVerilogImportError(m, import_err_msg) from e
      config.vprint(f"Successfully verilated the given model!", 2)

    else:
      config.vprint(f"{config.get_top_module()} not verilated because it's cached!", 2)

  #-----------------------------------------------------------------------
  # create_verilator_c_wrapper
  #-----------------------------------------------------------------------

  def create_verilator_c_wrapper( s, m, config, packed_ports, cached ):
    """Return the file name of generated C component wrapper.

    Create a C wrapper that calls verilator C API and provides interfaces
    that can be later called through CFFI.
    """
    component_name = config.get_top_module()
    dump_vcd = int(config.is_vl_trace_enabled())
    vcd_timescale = config.get_vl_trace_timescale()
    half_cycle_time = config.get_vl_trace_half_cycle_time()
    wrapper_name = config.get_c_wrapper_path()
    config.vprint("\n=====Generate C wrapper=====")

    # The wrapper template should be in the same directory as this file
    template_name = \
      os.path.dirname( os.path.abspath( __file__ ) ) + \
      os.path.sep + 'verilator_wrapper.c.template'

    # Generate port declarations for the verilated model in C
    port_defs = []
    for name, v_name, port in packed_ports:
      if v_name:
        port_defs.append( s.gen_signal_decl_c( v_name, port ) )
    port_cdefs = copy.copy( port_defs )
    make_indent( port_defs, 2 )
    port_defs = '\n'.join( port_defs )

    # Generate initialization statements for in/out ports
    port_inits = []
    for name, v_name, port in packed_ports:
      if v_name:
        port_inits.extend( s.gen_signal_init_c( v_name, port ) )
    make_indent( port_inits, 1 )
    port_inits = '\n'.join( port_inits )

    # Fill in the C wrapper template

    # Since we may run import with or without dump_vcd enabled, we need
    # to dump C wrapper regardless of whether the verilated model is
    # cached or not.
    # TODO: we can avoid dumping C wrapper if we attach some metadata to
    # tell if the wrapper was generated with or without `dump_vcd` enabled.
    with open( template_name, 'r' ) as template:
      with open( wrapper_name, 'w' ) as output:
        c_wrapper = template.read()
        c_wrapper = c_wrapper.format( **locals() )
        output.write( c_wrapper )

    config.vprint(f"Successfully generated C wrapper {wrapper_name}!", 2)
    return port_cdefs

  #-----------------------------------------------------------------------
  # create_shared_lib
  #-----------------------------------------------------------------------

  def create_shared_lib( s, m, config, cached ):
    """Return the name of compiled shared lib."""
    full_name = config.get_top_module()
    dump_vcd = config.is_vl_trace_enabled()
    config.vprint("\n=====Compile shared library=====")

    # Since we may run import with or without dump_vcd enabled, we need
    # to compile C wrapper regardless of whether the verilated model is
    # cached or not.
    # TODO: A better caching strategy is to attach some metadata
    # to the C wrapper so that we know the wrapper was generated with or
    # without dump_vcd enabled.
    if dump_vcd or not cached:
      cmd = config.create_cc_cmd()

      # Try to call the C compiler
      try:
        config.vprint("Compiling shared library with command:", 2)
        config.vprint(f"{cmd}", 4)
        subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True,
                                 universal_newlines=True )
      except subprocess.CalledProcessError as e:
        err_msg = e.output if not isinstance(e.output, bytes) else \
                  e.output.decode('utf-8')
        import_err_msg = \
            f"Failed to compile Verilated model into a shared library:\n"\
            f"  C compiler command:\n{indent(cmd, '  ')}\n\n"\
            f"  C compiler output:\n{indent(wrap(err_msg), '  ')}\n"
        raise SVerilogImportError(m, import_err_msg) from e
      config.vprint(f"Successfully compiled shared library "\
                    f"{config.get_shared_lib_path()}!", 2)

    else:
      config.vprint(f"Didn't compile shared library because it's cached!", 2)

  #-----------------------------------------------------------------------
  # create_py_wrapper
  #-----------------------------------------------------------------------

  def create_py_wrapper( s, m, config, rtype, packed_ports, port_cdefs, cached ):
    """Return the file name of the generated PyMTL component wrapper."""
    config.vprint("\n=====Generate PyMTL wrapper=====")

    # Load the wrapper template
    template_name = \
      os.path.dirname( os.path.abspath( __file__ ) ) + \
      os.path.sep + 'verilator_wrapper.py.template'
    wrapper_name = config.get_py_wrapper_path()

    # Port definitions of verilated model
    make_indent( port_cdefs, 4 )

    # Port definition in PyMTL style
    symbols, port_defs, connections = s.gen_signal_decl_py( rtype )
    make_indent( port_defs, 2 )
    make_indent( connections, 2 )
    # Wire definition in PyMTL style
    wire_defs = []
    for name, v_name, port in packed_ports:
      wire_defs.append( s.gen_wire_decl_py( name, port ) )
    make_indent( wire_defs, 2 )

    # Set upblk inputs and outputs
    set_comb_input = s.gen_comb_input( packed_ports )
    set_comb_output = s.gen_comb_output( packed_ports )
    make_indent( set_comb_input, 3 )
    make_indent( set_comb_output, 3 )

    # Generate constraints for sequential block
    constraints = s.gen_constraints( packed_ports )
    make_indent( constraints, 4 )
    constraint_str = '' if not constraints else \
"""\
constraint_list = [
{}
      ]

      s.add_constraints( *constraint_list )
""".format( '\n'.join( constraints ) )

    # Line trace
    line_trace = s.gen_line_trace_py( packed_ports )

    # Internal line trace
    in_line_trace = s.gen_internal_line_trace_py( packed_ports )

    # Fill in the python wrapper template
    if not cached:
      with open( template_name, 'r' ) as template:
        with open( wrapper_name, 'w' ) as output:
          py_wrapper = template.read()
          py_wrapper = py_wrapper.format(
            component_name  = config.get_top_module(),
            has_clk         = int(config.has_clk()),
            clk             = 'inv_clk' if not config.has_clk() else \
                              next(filter(lambda x: x[0]=='clk', packed_ports))[1],
            lib_file        = config.get_shared_lib_path(),
            port_cdefs      = ('  '*4+'\n').join( port_cdefs ),
            port_defs       = '\n'.join( port_defs ),
            wire_defs       = '\n'.join( wire_defs ),
            connections     = '\n'.join( connections ),
            set_comb_input  = '\n'.join( set_comb_input ),
            set_comb_output = '\n'.join( set_comb_output ),
            constraint_str  = constraint_str,
            line_trace      = line_trace,
            in_line_trace   = in_line_trace,
            dump_vcd        = int(config.is_vl_trace_enabled())
          )
          output.write( py_wrapper )

    config.vprint(f"Successfully generated PyMTL wrapper {wrapper_name}!", 2)
    return symbols

  #-----------------------------------------------------------------------
  # import_component
  #-----------------------------------------------------------------------

  def import_component( s, m, config, symbols ):
    """Return the PyMTL component imported from `wrapper_name`.sv."""
    config.vprint("=====Create python object=====")

    component_name = config.get_top_module()
    # Get the name of the wrapper Python module
    wrapper_name = config.get_py_wrapper_path()
    wrapper = wrapper_name.split('.')[0]

    # Add CWD to sys.path so we can import from the current directory
    if not os.getcwd() in sys.path:
      sys.path.append( os.getcwd() )

    # Check linecache in case the wrapper file has been modified
    linecache.checkcache()

    # Import the component from python wrapper

    if wrapper in sys.modules:
      # Reload the wrapper module in case the user has updated the wrapper
      reload(sys.modules[wrapper])
    else:
      # importlib.import_module inserts the wrapper module into sys.modules
      importlib.import_module(wrapper)

    # Try to access the top component class from the wrapper module
    try:
      imp_class = getattr( sys.modules[wrapper], component_name )
    except AttributeError as e:
      raise SVerilogImportError(m,
          f"internal error: PyMTL wrapper {wrapper_name} does not have "
          f"top component {component_name}!") from e

    imp = imp_class()
    config.vprint(f"Successfully created python object of {component_name}!", 2)

    # Update the global namespace of `construct` so that the struct and interface
    # classes defined previously can still be used in the imported model.
    imp.construct.__globals__.update( symbols )

    config.vprint("Import succeeds!")
    return imp

  #-------------------------------------------------------------------------
  # add_param_wrapper
  #-------------------------------------------------------------------------

  def add_param_wrapper( s, m, config, rtype, packed_ports ):
    outfile = f"{config.get_top_module()}.sv"
    parameters = config.get_v_param()

    with open(outfile, "w") as top_wrapper:
      # Port definitions of top-level wrapper
      ports = [
        f"  {p.get_direction()} logic [{p.get_dtype().get_length()}-1:0]"\
        f" {name}{'' if idx == len(packed_ports)-1 else ','}" \
        for idx, (_, name, p) in enumerate(packed_ports) if name
      ]
      # Parameters passed to the module to be parametrized
      params = [
        f"    .{param}( {val} ){'' if idx == len(parameters)-1 else ','}"\
        for idx, (param, val) in enumerate(parameters)
      ]
      # Connections between top module and inner module
      connect_ports = [
        f"    .{name}( {name} ){'' if idx == len(packed_ports)-1 else ','}"\
        for idx, (_, name, p) in enumerate(packed_ports) if name
      ]
      lines = [
        "// This is a top-level module that wraps a parametrized module",
        "// This file is generated by PyMTL SystemVerilog import pass",
        f'`include "{expand(config.get_param_include())}"',
        f"module {config.get_top_module()}",
        "(",
      ] + ports + [
        ");",
        f"  {config.get_module_to_parametrize()}",
        "  #(",
      ] + params + [
        "  ) wrapped_module",
        "  (",
      ] + connect_ports + [
        "  );",
        "endmodule",
      ]
      top_wrapper.write("\n".join(line for line in lines))
      top_wrapper.close()

  #-------------------------------------------------------------------------
  # gen_packed_ports
  #-------------------------------------------------------------------------

  def mangle_port( s, id_, port, n_dim ):
    if not n_dim:
      return [ ( id_, port ) ]
    else:
      return [ ( id_, rt.Array( n_dim, port ) ) ]

  def mangle_interface( s, id_, ifc, n_dim ):
    if not n_dim:
      ret = []
      all_properties = ifc.get_all_properties_packed()
      for name, rtype in all_properties:
        _n_dim, _rtype = s._get_rtype( rtype )
        if isinstance( _rtype, rt.Port ):
          ret += s.mangle_port( id_+"__"+name, _rtype, _n_dim )
        elif isinstance( _rtype, rt.InterfaceView ):
          ret += s.mangle_interface( id_+"__"+name, _rtype, _n_dim )
        else:
          assert False, f"{name} is not interface(s) or port(s)!"
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s.mangle_interface( id_+"__"+str(i), ifc, n_dim[1:] )
    return ret

  def gen_packed_ports( s, rtype ):
    """Return a list of (name, rt.Port ) that has all ports of `rtype`.

    This method performs SystemVerilog backend-specific name mangling and
    returns all ports that appear in the interface of component `rtype`.
    Each tuple contains a port or an array of port that has any data type
    allowed in RTLIRDataType.
    """
    packed_ports = []
    ports = rtype.get_ports_packed()
    ifcs = rtype.get_ifc_views_packed()
    for id_, port in ports:
      p_n_dim, p_rtype = s._get_rtype( port )
      packed_ports += s.mangle_port( id_, p_rtype, p_n_dim )
    for id_, ifc in ifcs:
      i_n_dim, i_rtype = s._get_rtype( ifc )
      packed_ports += s.mangle_interface( id_, i_rtype, i_n_dim )
    return packed_ports

  #-------------------------------------------------------------------------
  # gen_signal_decl_c
  #-------------------------------------------------------------------------

  def gen_signal_decl_c( s, name, port ):
    """Return C variable declaration of `port`."""
    c_dim = s._get_c_dim( port )
    nbits = s._get_c_nbits( port )
    UNSIGNED_8  = 'unsigned char'
    UNSIGNED_16 = 'unsigned short'
    UNSIGNED_32 = 'unsigned int'
    if sys.maxsize > 2**32:
      UNSIGNED_64 = 'unsigned long'
    else:
      UNSIGNED_64 = 'unsigned long long'
    if    nbits <= 8:  data_type = UNSIGNED_8
    elif  nbits <= 16: data_type = UNSIGNED_16
    elif  nbits <= 32: data_type = UNSIGNED_32
    elif  nbits <= 64: data_type = UNSIGNED_64
    else:              data_type = UNSIGNED_32
    name = s._verilator_name( name )
    return f'{data_type} * {name}{c_dim};'

  #-------------------------------------------------------------------------
  # gen_signal_init_c
  #-------------------------------------------------------------------------

  def gen_signal_init_c( s, name, port ):
    """Return C port variable initialization."""
    ret       = []
    c_dim     = s._get_c_dim( port )
    nbits     = s._get_c_nbits( port )
    deference = '&' if nbits <= 64 else ''
    name      = s._verilator_name( name )

    if c_dim:
      n_dim_size = s._get_c_n_dim( port )
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
        sub += f"[i_{idx}]"

      ret.append( assign_template.format( **locals() ) )

      # Indent the for loop
      for start, dim_size in enumerate( n_dim_size ):
        for idx in range( start + 1, len( n_dim_size ) + 1 ):
          ret[ idx ] = "  " + ret[ idx ]

    else:
      ret.append(f'm->{name} = {deference}model->{name};')

    return ret

  #-----------------------------------------------------------------------
  # Methods that generate python signal connections
  #-----------------------------------------------------------------------
  # Ports and interfaces will have the same name; their name-mangled
  # counterparts will have a mangled name starting with 'mangled__'.

  def gen_vector_conns( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    l, r = pos, pos+nbits
    _lhs, _rhs = s._verilator_name(lhs), s._verilator_name(rhs)
    ret = [f"connect( s.{_lhs}, s.mangled__{_rhs}[{l}:{r}] )"]
    return ret, r

  def gen_struct_conns( s, d, lhs, rhs, dtype, pos, symbols ):
    dtype_name = dtype.get_class().__name__
    upblk_name = lhs.replace('.', '_DOT_').replace('[', '_LBR_').replace(']', '_RBR_')
    ret = [
      "@s.update",
      f"def {upblk_name}():",
    ]
    if d == "output":
      ret.append( f"  s.{lhs} = {dtype_name}()" )
    # Patch `dtype_name` into the symbol dictionary
    if dtype_name not in symbols:
      symbols[dtype_name] = dtype.get_class()
    body = []
    all_properties = reversed(list(dtype.get_all_properties().items()))
    for name, field in all_properties:
      _ret, pos = s._gen_dtype_conns( d, lhs+"."+name, rhs, field, pos )
      body += _ret
    return ret + body, pos

  def _gen_vector_conns( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    l, r = pos, pos+nbits
    _lhs, _rhs = s._verilator_name( lhs ), s._verilator_name( rhs )
    if d == "input":
      ret = [f"  s.mangled__{_rhs}[{l}:{r}] = s.{_lhs}"]
    else:
      ret = [f"  s.{_lhs} = s.mangled__{_rhs}[{l}:{r}]"]
    return ret, r

  def _gen_struct_conns( s, d, lhs, rhs, dtype, pos ):
    ret = []
    all_properties = reversed(list(dtype.get_all_properties().items()))
    for field_name, field in all_properties:
      _ret, pos = s._gen_dtype_conns(d, lhs+"."+field_name, rhs, field, pos)
      ret += _ret
    return ret, pos

  def _gen_packed_array_conns( s, d, lhs, rhs, dtype, n_dim, pos ):
    if not n_dim:
      return s._gen_dtype_conns( d, lhs, rhs, dtype, pos )
    else:
      ret = []
      for idx in range(n_dim[0]):
        _lhs = lhs + f"[{idx}]"
        _ret, pos = \
          s._gen_packed_array_conns( d, _lhs, rhs, dtype, n_dim[1:], pos )
        ret += _ret
      return ret, pos

  def _gen_dtype_conns( s, d, lhs, rhs, dtype, pos ):
    if isinstance( dtype, rdt.Vector ):
      return s._gen_vector_conns( d, lhs, rhs, dtype, pos )
    elif isinstance( dtype, rdt.Struct ):
      return s._gen_struct_conns( d, lhs, rhs, dtype, pos )
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return s._gen_packed_array_conns( d, lhs, rhs, sub_dtype, n_dim, pos )
    else:
      assert False, f"unrecognized data type {dtype}!"

  def gen_dtype_conns( s, d, lhs, rhs, dtype, pos, symbols ):
    if isinstance( dtype, rdt.Vector ):
      return s.gen_vector_conns( d, lhs, rhs, dtype, pos )
    elif isinstance( dtype, rdt.Struct ):
      return s.gen_struct_conns( d, lhs, rhs, dtype, pos, symbols )
    else:
      assert False, f"unrecognized data type {dtype}!"

  def gen_port_conns( s, id_py, id_v, port, n_dim, symbols ):
    if not n_dim:
      d = port.get_direction()
      dtype = port.get_dtype()
      nbits = dtype.get_length()
      ret, pos = s.gen_dtype_conns( d, id_py, id_v, dtype, 0, symbols )
      assert pos == nbits, \
        f"internal error: {id_py} wire length mismatch!"
      return ret
    else:
      ret = []
      for idx in range(n_dim[0]):
        _id_py = id_py + f"[{idx}]"
        _id_v = id_v + f"[{idx}]"
        ret += s.gen_port_conns( _id_py, _id_v, port, n_dim[1:], symbols )
      return ret

  def gen_ifc_conns( s, id_py, id_v, ifc, n_dim, symbols ):
    if not n_dim:
      ret = []
      all_properties = ifc.get_all_properties_packed()
      for name, rtype in all_properties:
        _n_dim, _rtype = s._get_rtype( rtype )
        _id_py = id_py + f".{name}"
        _id_v = id_v + f"__{name}"
        if isinstance( _rtype, rt.Port ):
          ret += s.gen_port_conns( _id_py, _id_v, _rtype, _n_dim, symbols )
        else:
          ret += s.gen_ifc_conns( _id_py, _id_v, _rtype, _n_dim, symbols )
      return ret
    else:
      ret = []
      for idx in range( n_dim[0] ):
        _id_py = id_py + f"[{idx}]"
        _id_v = id_v + f"__{idx}"
        ret += s.gen_ifc_conns( _id_py, _id_v, ifc, n_dim[1:], symbols )
      return ret

  #-------------------------------------------------------------------------
  # gen_signal_decl_py
  #-------------------------------------------------------------------------

  def gen_signal_decl_py( s, rtype ):
    """Return the PyMTL definition of all interface ports of `rtype`."""

    #-----------------------------------------------------------------------
    # Methods that generate signal declarations
    #-----------------------------------------------------------------------

    def gen_dtype_str( symbols, dtype ):
      if isinstance( dtype, rdt.Vector ):
        nbits = dtype.get_length()
        Bits_name = f"Bits{nbits}"
        if Bits_name not in symbols and nbits >= 256:
          Bits_class = mk_bits( nbits )
          symbols.update( { Bits_name : Bits_class } )
        return f'Bits{dtype.get_length()}'
      elif isinstance( dtype, rdt.Struct ):
        # It is possible to reuse the existing struct class because its __init__
        # can be called without arguments.
        name, cls = dtype.get_name(), dtype.get_class()
        if name not in symbols:
          symbols.update( { name : cls } )
        return name
      else:
        assert False, f"unrecognized data type {dtype}!"

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
              rhs = f"[ {rhs} for _ in range({length}) ]"
          else:
            rhs = "{direction}( {dtype} )"
            port = _port
          direction = s._get_direction( port )
          dtype = gen_dtype_str( symbols, port.get_dtype() )
          rhs = rhs.format( **locals() )
          decls.append(f"s.{id_} = {rhs}")
      return symbols, decls

    def gen_ifc_decl_py( ifcs ):

      def gen_ifc_str( symbols, ifc ):

        def _get_arg_str( name, obj ):
          if isinstance( obj, int ):
            return str(obj)
          elif isinstance( obj, Bits ):
            nbits = obj.nbits
            value = int(obj)
            Bits_name = f"Bits{nbits}"
            Bits_arg_str = f"{Bits_name}( {value} )"
            if Bits_name not in symbols and nbits >= 256:
              Bits_class = mk_bits( nbits )
              symbols.update( { Bits_name : Bits_class } )
            return Bits_arg_str
          elif is_bitstruct_inst( obj ):
            raise TypeError("Do you really want to pass in an instance of "
                            "a BitStruct? Contact PyMTL developers!")
            # This is hacky: we don't know how to construct an object that
            # is the same as `obj`, but we do have the object itself. If we
            # add `obj` to the namespace of `construct` everything works fine
            # but the user cannot tell what object is passed to the constructor
            # just from the code.
            # Do not use a double underscore prefix because that will be
            # interpreted differently by the Python interpreter
            # bs_name = ("_" if name[0] != "_" else "") + name + "_obj"
            # if bs_name not in symbols:
              # symbols.update( { bs_name : obj } )
            # return bs_name
          elif isinstance( obj, type ) and issubclass( obj, Bits ):
            nbits = obj.nbits
            Bits_name = f"Bits{nbits}"
            if Bits_name not in symbols and nbits >= 256:
              Bits_class = mk_bits( nbits )
              symbols.update( { Bits_name : Bits_class } )
            return Bits_name
          elif is_bitstruct_class(obj):
            BitStruct_name = obj.__name__
            if BitStruct_name not in symbols:
              symbols.update( { BitStruct_name : obj } )
            return BitStruct_name

          raise TypeError( f"Interface constructor argument {obj} is not an int/Bits/BitStruct!" )

        name, cls = ifc.get_name(), ifc.get_class()
        if name not in symbols:
          symbols.update( { name : cls } )
        arg_list = []
        args = ifc.get_args()
        for idx, obj in enumerate(args[0]):
          arg_list.append( _get_arg_str( f"_ifc_arg{idx}", obj ) )
        for arg_name, arg_obj in args[1].items():
          arg_list.append( f"{arg_name} = {_get_arg_str( arg_name, arg_obj )}" )
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
            rhs = f"[ {rhs} for _ in range({length}) ]"
        else:
          rhs = "{ifc_class}({ifc_params})"
          _ifc = ifc
        ifc_class, ifc_params = gen_ifc_str( symbols, _ifc )
        if ifc_params:
          ifc_params = " " + ifc_params + " "
        rhs = rhs.format( **locals() )
        decls.append(f"s.{id_} = {rhs}")
      return symbols, decls

    #-----------------------------------------------------------------------
    # Method gen_signal_decl_py
    #-----------------------------------------------------------------------

    ports = rtype.get_ports_packed()
    ifcs = rtype.get_ifc_views_packed()

    p_symbols, p_decls = gen_port_decl_py( ports )
    i_symbols, i_decls = gen_ifc_decl_py( ifcs )

    p_conns, i_conns = [], []
    struct_conn_symbols = {}
    for id_, port in ports:
      p_n_dim, p_rtype = s._get_rtype( port )
      p_conns += s.gen_port_conns( id_, id_, p_rtype, p_n_dim, struct_conn_symbols )
    for id_, ifc in ifcs:
      i_n_dim, i_rtype = s._get_rtype( ifc )
      i_conns += s.gen_ifc_conns( id_, id_, i_rtype, i_n_dim, struct_conn_symbols )

    p_symbols.update( i_symbols )
    p_symbols.update( struct_conn_symbols )
    decls = p_decls + i_decls
    conns = p_conns + i_conns

    return p_symbols, decls, conns

  #-------------------------------------------------------------------------
  # gen_wire_decl_py
  #-------------------------------------------------------------------------

  def gen_wire_decl_py( s, name, _wire ):
    """Return the PyMTL definition of `wire`."""
    template = "s.mangled__{name} = {rhs}"
    rhs = "Wire( Bits{nbits} )"
    name = s._verilator_name( name )
    n_dim, rtype = s._get_rtype( _wire )
    dtype = rtype.get_dtype()
    nbits = dtype.get_length()
    for idx in reversed(n_dim):
      rhs = f"[ {rhs} for _ in range({idx}) ]"
    rhs = rhs.format( **locals() )
    return template.format( **locals() )

  #-------------------------------------------------------------------------
  # gen_comb_input
  #-------------------------------------------------------------------------

  def gen_port_array_input( s, lhs, rhs, dtype, n_dim ):
    nbits = dtype.get_length()
    if not n_dim:
      return s._gen_ref_write( lhs, rhs, nbits )
    else:
      ret = []
      for idx in range( n_dim[0] ):
        _lhs = f"{lhs}[{idx}]"
        _rhs = f"{rhs}[{idx}]"
        ret += s.gen_port_array_input( _lhs, _rhs, dtype, n_dim[1:] )
      return ret

  def gen_comb_input( s, packed_ports ):
    ret = []
    # Read all input ports ( except for 'clk' ) from component ports into
    # the verilated model. We do NOT want `clk` signal to be read into
    # the verilated model because only the sequential update block of
    # the imported component should manipulate it.
    for py_name, v_name, rtype in packed_ports:
      p_n_dim, p_rtype = s._get_rtype( rtype )
      if s._get_direction( p_rtype ) == 'InPort' and py_name != 'clk' and v_name:
        dtype = p_rtype.get_dtype()
        lhs = "_ffi_m."+s._verilator_name(v_name)
        rhs = "s.mangled__"+s._verilator_name(py_name)
        ret += s.gen_port_array_input( lhs, rhs, dtype, p_n_dim )
    return ret

  #-------------------------------------------------------------------------
  # gen_comb_output
  #-------------------------------------------------------------------------

  def gen_port_array_output( s, lhs, rhs, dtype, n_dim ):
    nbits = dtype.get_length()
    if not n_dim:
      return s._gen_ref_read( lhs, rhs, nbits )
    else:
      ret = []
      for idx in range( n_dim[0] ):
        _lhs = f"{lhs}[{idx}]"
        _rhs = f"{rhs}[{idx}]"
        ret += s.gen_port_array_output( _lhs, _rhs, dtype, n_dim[1:] )
      return ret

  def gen_comb_output( s, packed_ports ):
    ret = []
    for py_name, v_name, rtype in packed_ports:
      p_n_dim, p_rtype = s._get_rtype( rtype )
      if s._get_direction( rtype ) == 'OutPort':
        dtype = p_rtype.get_dtype()
        lhs = "s.mangled__" + s._verilator_name(py_name)
        rhs = "_ffi_m." + s._verilator_name(v_name)
        ret += s.gen_port_array_output( lhs, rhs, dtype, p_n_dim )
    return ret

  #-------------------------------------------------------------------------
  # gen_constraints
  #-------------------------------------------------------------------------

  def _gen_constraints( s, name, n_dim, rtype ):
    if not n_dim:
      return [f"U( seq_upblk ) < RD( s.mangled__{name} ),"]
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s._gen_constraints( f"{name}[{i}]", n_dim[1:], rtype )
      return ret

  def gen_constraints( s, packed_ports ):
    ret = []
    for py_name, v_name, rtype in packed_ports:
      if s._get_direction( rtype ) == 'OutPort':
        if isinstance( rtype, rt.Array ):
          n_dim = rtype.get_dim_sizes()
          sub_type = rtype.get_sub_type()
          ret += s._gen_constraints( py_name, n_dim, sub_type )
        else:
          wire_name = "s.mangled__" + s._verilator_name(py_name)
          ret.append( f"U( seq_upblk ) < RD( {wire_name} )," )
    ret.append( "U( seq_upblk ) < U( comb_upblk )," )
    return ret

  #-------------------------------------------------------------------------
  # gen_line_trace_py
  #-------------------------------------------------------------------------

  def gen_line_trace_py( s, packed_ports ):
    """Return the line trace method body that shows all interface ports."""
    ret = [ 'lt = ""' ]
    template = 'lt += "{my_name} = {{}}, ".format({full_name})'
    for name, v_name, port in packed_ports:
      my_name = name
      full_name = 's.mangled__'+s._verilator_name(name)
      ret.append( template.format( **locals() ) )
    ret.append( 'return lt' )
    make_indent( ret, 2 )
    return '\n'.join( ret )

  #-------------------------------------------------------------------------
  # gen_internal_line_trace_py
  #-------------------------------------------------------------------------

  def gen_internal_line_trace_py( s, packed_ports ):
    """Return the line trace method body that shows all CFFI ports."""
    ret = [ '_ffi_m = s._ffi_m', 'lt = ""' ]
    template = \
      "lt += '{v_name} = {{}}, '.format(full_vector(s.mangled__{my_name}, _ffi_m.{v_name}))"
    for my_name, v_name, port in packed_ports:
      if v_name:
        my_name = s._verilator_name(my_name)
        v_name = s._verilator_name(v_name)
        ret.append( template.format(**locals()) )
    ret.append( 'return lt' )
    make_indent( ret, 2 )
    return '\n'.join( ret )

  #=========================================================================
  # Helper functions
  #=========================================================================

  def _verilator_name( s, name ):
    # TODO: PyMTL translation should generate dollar-sign-free Verilog source
    # code. Verify that this replacement rule here is not necessary.
    return name.replace('__', '___05F').replace('$', '__024')

  def _get_direction( s, port ):
    if isinstance( port, rt.Port ):
      d = port.get_direction()
    elif isinstance( port, rt.Array ):
      d = port.get_sub_type().get_direction()
    else:
      assert False, f"{port} is not a port or array of ports!"
    if d == 'input':
      return 'InPort'
    elif d == 'output':
      return 'OutPort'
    else:
      assert False, f"unrecognized direction {d}!"

  def _get_c_n_dim( s, port ):
    if isinstance( port, rt.Array ):
      return port.get_dim_sizes()
    else:
      return []

  def _get_c_dim( s, port ):
    return "".join( f"[{i}]" for i in s._get_c_n_dim(port) )

  def _get_c_nbits( s, port ):
    if isinstance( port, rt.Array ):
      dtype = port.get_sub_type().get_dtype()
    else:
      dtype = port.get_dtype()
    return dtype.get_length()

  def _gen_ref_write( s, lhs, rhs, nbits ):
    if nbits <= 64:
      return [ f"{lhs}[0] = int({rhs})" ]
    else:
      ret = []
      ITEM_BITWIDTH = 32
      num_assigns = (nbits-1)//ITEM_BITWIDTH+1
      for idx in range(num_assigns):
        l = ITEM_BITWIDTH*idx
        r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
        ret.append( f"{lhs}[{idx}] = int({rhs}[{l}:{r}])" )
      return ret

  def _gen_ref_read( s, lhs, rhs, nbits ):
    if nbits <= 64:
      return [ f"{lhs} = Bits{nbits}({rhs}[0])" ]
    else:
      ret = []
      ITEM_BITWIDTH = 32
      num_assigns = (nbits-1)//ITEM_BITWIDTH+1
      for idx in range(num_assigns):
        l = ITEM_BITWIDTH*idx
        r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
        _nbits = r - l
        ret.append( f"{lhs}[{l}:{r}] = Bits{_nbits}({rhs}[{idx}])" )
      return ret

  def _get_rtype( s, _rtype ):
    if isinstance( _rtype, rt.Array ):
      n_dim = _rtype.get_dim_sizes()
      rtype = _rtype.get_sub_type()
    else:
      n_dim = []
      rtype = _rtype
    return n_dim, rtype
