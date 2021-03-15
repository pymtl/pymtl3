#=========================================================================
# VerilogVerilatorImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 25, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""

import copy
import importlib
import json
import linecache
import os
import shutil
import subprocess
import sys
import timeit
from functools import reduce
from importlib import reload
from itertools import cycle
from textwrap import indent

from pymtl3 import MetadataKey
from pymtl3.datatypes import Bits, is_bitstruct_class, is_bitstruct_inst, mk_bits
from pymtl3.dsl import Component
from pymtl3.dsl.errors import UnsetMetadataError
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRGetter
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.rtype.RTLIRDataType import _get_rtlir_dtype_struct

from ..errors import VerilogImportError
from ..util.utility import (
    expand,
    gen_mapped_ports,
    get_component_unique_name,
    get_rtype,
    make_indent,
    wrap,
)
from ..VerilogPlaceholderPass import VerilogPlaceholderPass
from .verilator_wrapper_c_template import template as c_template
from .verilator_wrapper_py_template import template as py_template


class VerilogVerilatorImportPass( BasePass ):
  """Import an arbitrary SystemVerilog module as a PyMTL component."""

  # Import pass input pass data

  #: Enable import on a component.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  enable              = MetadataKey(bool)

  #: Print out extra debug information during import.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  verbose             = MetadataKey(bool)

  #: Spend more time on compilation for faster simulation performance
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  fast                = MetadataKey(bool)

  #: Use Verilog ``line_trace`` output as the Python line_trace return value.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_line_trace       = MetadataKey(bool)

  #: Enable Verilator coverage.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_coverage         = MetadataKey(bool)

  #: Enable Verilator line coverage.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_line_coverage    = MetadataKey(bool)

  #: Enable Verilator toggle coverage.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_toggle_coverage  = MetadataKey(bool)

  #: Specify the Verilator make directory.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: obj_<top-component-name>
  vl_mk_dir           = MetadataKey(str)

  #: Enable Verilog assert.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_enable_assert    = MetadataKey(bool)

  #: Verilator optimization level.
  #:
  #: Type: ``int``; input
  #:
  #: Default value: ``3``
  vl_opt_level        = MetadataKey(int)

  #: Verilator unroll count.
  #:
  #: Type: ``int``; input
  #:
  #: Default value: ``1000000``
  vl_unroll_count     = MetadataKey(int)

  #: Verilator unroll statement count.
  #:
  #: Type: ``int``; input
  #:
  #: Default value: ``1000000``
  vl_unroll_stmts     = MetadataKey(int)

  #: Enable Verilator lint warnings.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``True``
  vl_W_lint           = MetadataKey(bool)

  #: Enable Verilator style warnings.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``True``
  vl_W_style          = MetadataKey(bool)

  #: Enable Verilator fatal warnings.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``True``
  vl_W_fatal          = MetadataKey(bool)

  #: A list of suppressed Verilator warnings.
  #:
  #: Type: ``[str]``; input
  #:
  #: Default value: ``['UNSIGNED', 'UNOPTFLAT', 'WIDTH']``
  vl_Wno_list         = MetadataKey(list)

  #: Verilator initialization options.
  #:
  #: Possible values: ``'ones'``, ``'zeros'``, ``'rand'``, and non-zero integers; input
  #:
  #: Default value: ``'zeros'``
  vl_xinit            = MetadataKey(str)

  #: Enable Verilator VCD tracing.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_trace            = MetadataKey(bool)

  #: Filename of Verilator VCD tracing.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: translated-component-name.verilator1
  vl_trace_filename   = MetadataKey(str)

  #: Time scale of generated Verilator VCD.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ``'10ps'``
  vl_trace_timescale  = MetadataKey(str)

  #: Cycle time of PyMTL clk pin in the generated Verilator VCD in unit of ``vl_trace_timescale``.
  #:
  #: Type: ``int``; input
  #:
  #: Default value: ``100``
  vl_trace_cycle_time = MetadataKey(int)

  #: Set to true to allow for on-demand VCD dumping
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  vl_trace_on_demand  = MetadataKey(bool)

  #: Top level port name that is used to enable VCD dumping when
  #: `vl_trace_on_demand` is True. Assuming the port is an active-high
  #: enable signal.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ``""``
  vl_trace_on_demand_portname = MetadataKey(str)

  #: Optional flags to be passed to the C compiler.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ``''``
  c_flags             = MetadataKey(str)

  #: Optional include paths to be passed to the C compiler.
  #:
  #: Type: ``[str]``; input
  #:
  #: Default value: ``[]``
  c_include_path      = MetadataKey(list)

  #: Optional source file paths to be passed to the C compiler.
  #:
  #: Type: ``[str]``; input
  #:
  #: Default value: ``[]``
  c_srcs              = MetadataKey(list)

  #: Optional flags to be passed to LD.
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ``''``
  ld_flags            = MetadataKey(str)

  #: Optional libraries to be passed to LD (e.g., ``'-lfoo'``).
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ``''``
  ld_libs             = MetadataKey(str)

  # Import pass output pass data

  #: An instnace of :class:`VerilatorImportConfigs` containing the parsed options.
  #:
  #: Type: :class:`VerilatorImportConfigs`; output
  import_config       = MetadataKey()

  def __call__( s, top ):
    """Import the PyMTL component hierarhcy rooted at ``top``."""
    s.top = top
    if not top._dsl.constructed:
      raise VerilogImportError( top,
        f"please elaborate design {top} before applying the import pass!" )
    ret = s.traverse_hierarchy( top )
    if ret is None:
      ret = top
    else:
      ret.elaborate()
    return ret

  def traverse_hierarchy( s, m ):
    c = s.__class__
    ph_pass = c.get_placeholder_pass()
    # Import can only be performed on Placeholders
    if m.has_metadata( ph_pass.enable ) and m.get_metadata( ph_pass.enable ):
      m.set_metadata( c.import_config, c.get_import_config()( m ) )
      return s.do_import( m )

    else:
      for child in m.get_child_components(repr):
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
      raise VerilogImportError( m, msg )

  #-----------------------------------------------------------------------
  # Backend-specific methods
  #-----------------------------------------------------------------------

  @staticmethod
  def get_backend_name():
    return "verilog"

  @staticmethod
  def get_placeholder_pass():
    return VerilogPlaceholderPass

  @staticmethod
  def get_translation_pass():
    from ..translation.VerilogTranslationPass import VerilogTranslationPass
    return VerilogTranslationPass

  @staticmethod
  def get_import_config():
    from .VerilogVerilatorImportConfigs import VerilogVerilatorImportConfigs
    return VerilogVerilatorImportConfigs

  @staticmethod
  def get_gen_mapped_port():
    return gen_mapped_ports

  #-----------------------------------------------------------------------
  # is_cached
  #-----------------------------------------------------------------------

  def is_cached( s, m, ip_cfg ):
    c = s.__class__
    # Only components translated by pymtl translation passes will be cached
    try:
      is_same = m.get_metadata( c.get_translation_pass().is_same )
    except UnsetMetadataError:
      is_same = False

    # Check if the verilated model is cached
    is_source_cached = False
    obj_dir = ip_cfg.vl_mk_dir
    c_wrapper = ip_cfg.get_c_wrapper_path()
    py_wrapper = ip_cfg.get_py_wrapper_path()
    shared_lib = ip_cfg.get_shared_lib_path()
    if is_same and os.path.exists(obj_dir) and os.path.exists(c_wrapper) and \
       os.path.exists(py_wrapper) and os.path.exists(shared_lib):
      is_source_cached = True

    # Check if the configurations from the last run are the same
    is_config_cached = False
    config_file = f'pymtl_import_config_{ip_cfg.translated_top_module}.json'
    new_cfg = s.serialize_cfg( ip_cfg )
    if os.path.exists(config_file):
      with open(config_file) as fd:
        if s.is_same_cfg( json.load( fd ), new_cfg ):
          is_config_cached = True

    return is_source_cached and is_config_cached, config_file, new_cfg

  #-----------------------------------------------------------------------
  # get_imported_object
  #-----------------------------------------------------------------------

  def get_imported_object( s, m ):
    c = s.__class__
    ph_cfg = m.get_metadata( c.get_placeholder_pass().placeholder_config )
    ip_cfg = m.get_metadata( c.import_config )
    ip_cfg.setup_configs( m, c.get_translation_pass(), c.get_placeholder_pass() )

    rtype = RTLIRGetter(cache=False).get_component_ifc_rtlir( m )

    # Now we selectively unpack array of ports if they are referred to in
    # port_map
    ports = c.get_gen_mapped_port()( m, ph_cfg.port_map,
                                     ph_cfg.has_clk, ph_cfg.has_reset,
                                     ph_cfg.separator )

    cached, config_file, cfg_d = s.is_cached( m, ip_cfg )

    s.create_verilator_model( m, ph_cfg, ip_cfg, cached )

    port_cdefs = s.create_verilator_c_wrapper( m, ph_cfg, ip_cfg, ports, cached )

    s.create_shared_lib( m, ph_cfg, ip_cfg, cached )

    symbols = s.create_py_wrapper( m, ph_cfg, ip_cfg, rtype, ports, port_cdefs, cached )

    imp = s.import_component( m, ph_cfg, ip_cfg, symbols )

    imp._ip_cfg = ip_cfg
    imp._ph_cfg = ph_cfg
    imp._ports = ports

    # Dump configuration dict to config_file
    with open( config_file, 'w' ) as fd:
      json.dump( cfg_d, fd, indent = 4 )

    return imp

  #-----------------------------------------------------------------------
  # create_verilator_model
  #-----------------------------------------------------------------------

  def create_verilator_model( s, m, ph_cfg, ip_cfg, cached ):
    # Verilate module `m`.

    ip_cfg.vprint("\n=====Verilate model=====")

    if not cached:
      # Generate verilator command
      cmd = ip_cfg.create_vl_cmd()

      # Remove obj_dir directory if it already exists.
      # obj_dir is where the verilator output ( C headers and sources ) is stored
      obj_dir = ip_cfg.vl_mk_dir
      if os.path.exists( obj_dir ):
        shutil.rmtree( obj_dir )

      succeeds = True

      # Try to call verilator
      try:
        ip_cfg.vprint(f"Verilating {ip_cfg.translated_top_module} with command:", 2)
        ip_cfg.vprint(f"{cmd}", 4)
        t0 = timeit.default_timer()
        subprocess.check_output(
            cmd, stderr = subprocess.STDOUT, shell = True )
        ip_cfg.vprint(f"verilate time: {timeit.default_timer()-t0}")
      except subprocess.CalledProcessError as e:
        succeeds = False
        err_msg = e.output if not isinstance(e.output, bytes) else \
                  e.output.decode('utf-8')
        import_err_msg = \
            f"Fail to verilate model {ip_cfg.translated_top_module}\n"\
            f"  Verilator command:\n{indent(cmd, '  ')}\n\n"\
            f"  Verilator output:\n{indent(wrap(err_msg), '  ')}\n"

      if not succeeds:
        raise VerilogImportError(m, import_err_msg)

      ip_cfg.vprint("Successfully verilated the given model!", 2)

    else:
      ip_cfg.vprint(f"{ip_cfg.translated_top_module} not verilated because it's cached!", 2)

  #-----------------------------------------------------------------------
  # create_verilator_c_wrapper
  #-----------------------------------------------------------------------

  def create_verilator_c_wrapper( s, m, ph_cfg, ip_cfg, ports, cached ):
    # Return the file name of generated C component wrapper.
    # Create a C wrapper that calls verilator C API and provides interfaces
    # that can be later called through CFFI.

    component_name = ip_cfg.translated_top_module
    vl_component_name = s._verilator_name(component_name)
    dump_vcd = int(ip_cfg.vl_trace)
    vcd_timescale = ip_cfg.vl_trace_timescale
    half_cycle_time = ip_cfg.vl_trace_cycle_time // 2
    external_trace = int(ip_cfg.vl_line_trace)
    wrapper_name = ip_cfg.get_c_wrapper_path()
    verilator_xinit_value = ip_cfg.get_vl_xinit_value()
    verilator_xinit_seed = ip_cfg.get_vl_xinit_seed()
    has_clk = int(ph_cfg.has_clk)

    # On-demand VCD dumping configs
    on_demand_dump_vcd = int(ip_cfg.vl_trace_on_demand)
    on_demand_vcd_enable = str(ip_cfg.vl_trace_on_demand_portname)
    if on_demand_vcd_enable:
      on_demand_vcd_enable = f"model->{on_demand_vcd_enable}"
    else:
      on_demand_vcd_enable = 0

    ip_cfg.vprint("\n=====Generate C wrapper=====")

    # Generate port declarations for the verilated model in C
    port_defs = []
    for _, v_name, port, _ in ports:
      if v_name:
        port_defs.append( s.gen_signal_decl_c( v_name, port ) )
    port_cdefs = copy.copy( port_defs )
    make_indent( port_defs, 2 )
    port_defs = '\n'.join( port_defs )

    # Generate initialization statements for in/out ports
    port_inits = []
    for _, v_name, port, _ in ports:
      if v_name:
        port_inits.extend( s.gen_signal_init_c( v_name, port ) )
    make_indent( port_inits, 1 )
    port_inits = '\n'.join( port_inits )

    # Fill in the C wrapper template
    with open( wrapper_name, 'w' ) as output:
      output.write( c_template.format( **locals() ) )

    ip_cfg.vprint(f"Successfully generated C wrapper {wrapper_name}!", 2)
    return port_cdefs

  #-----------------------------------------------------------------------
  # create_shared_lib
  #-----------------------------------------------------------------------

  def create_shared_lib( s, m, ph_cfg, ip_cfg, cached ):
    # Return the name of compiled shared lib.

    full_name = ip_cfg.translated_top_module
    dump_vcd = ip_cfg.vl_trace
    ip_cfg.vprint("\n=====Compile shared library=====")

    if not cached:
      cmd = ip_cfg.create_cc_cmd()

      succeeds = True

      # Try to call the C compiler
      try:
        ip_cfg.vprint("Compiling shared library with command:", 2)
        ip_cfg.vprint(f"{cmd}", 4)
        t0 = timeit.default_timer()
        subprocess.check_output(
            cmd,
            stderr = subprocess.STDOUT,
            shell = True,
            universal_newlines = True
        )
        ip_cfg.vprint(f"shared library compilation time: {timeit.default_timer()-t0}")
      except subprocess.CalledProcessError as e:
        succeeds = False
        err_msg = e.output if not isinstance(e.output, bytes) else \
                  e.output.decode('utf-8')
        import_err_msg = \
            f"Failed to compile Verilated model into a shared library:\n"\
            f"  C compiler command:\n{indent(cmd, '  ')}\n\n"\
            f"  C compiler output:\n{indent(wrap(err_msg), '  ')}\n"

      if not succeeds:
        raise VerilogImportError(m, import_err_msg)

      ip_cfg.vprint(f"Successfully compiled shared library "\
                    f"{ip_cfg.get_shared_lib_path()}!", 2)

    else:
      ip_cfg.vprint("Didn't compile shared library because it's cached!", 2)

  #-----------------------------------------------------------------------
  # create_py_wrapper
  #-----------------------------------------------------------------------
  # Return the file name of the generated PyMTL component wrapper.

  def create_py_wrapper( s, m, ph_cfg, ip_cfg, rtype, ports, port_cdefs, cached ):
    ip_cfg.vprint("\n=====Generate PyMTL wrapper=====")

    wrapper_name = ip_cfg.get_py_wrapper_path()

    # Port definitions of verilated model
    make_indent( port_cdefs, 4 )

    # Port definition in PyMTL style
    symbols, port_defs = s.gen_signal_decl_py( rtype )
    make_indent( port_defs, 2 )

    # Set upblk inputs and outputs
    set_comb_input, structs_input   = s.gen_comb_input( ports, symbols )
    set_comb_output, structs_output = s.gen_comb_output( ports, symbols )
    make_indent( structs_input, 2 )
    make_indent( structs_output, 2 )
    make_indent( set_comb_input, 3 )
    make_indent( set_comb_output, 3 )

    # Line trace
    line_trace = s.gen_line_trace_py( ports )

    # Internal line trace
    in_line_trace = s.gen_internal_line_trace_py( ports )

    # External trace function definition
    if ip_cfg.vl_line_trace:
      external_trace_c_def = f'void trace( V{ip_cfg.translated_top_module}_t *, char * );'
    else:
      external_trace_c_def = ''

    # Fill in the python wrapper template
    with open( wrapper_name, 'w' ) as output:
      py_wrapper = py_template.format(
        component_name        = ip_cfg.translated_top_module,
        has_clk               = int(ph_cfg.has_clk),
        clk                   = 'inv_clk' if not ph_cfg.has_clk else \
                                next(filter(lambda x: x[0][0]=='clk', ports))[1],
        lib_file              = ip_cfg.get_shared_lib_path(),
        port_cdefs            = ('  '*4+'\n').join( port_cdefs ),
        port_defs             = '\n'.join( port_defs ),
        structs_input         = '\n'.join( structs_input ),
        structs_output        = '\n'.join( structs_output ),
        set_comb_input        = '\n'.join( set_comb_input ),
        set_comb_output       = '\n'.join( set_comb_output ),
        line_trace            = line_trace,
        in_line_trace         = in_line_trace,
        dump_vcd              = int(ip_cfg.vl_trace),
        has_vl_trace_filename = bool(ip_cfg.vl_trace_filename),
        vl_trace_filename     = ip_cfg.vl_trace_filename,
        external_trace        = int(ip_cfg.vl_line_trace),
        trace_c_def           = external_trace_c_def,
      )
      output.write( py_wrapper )

    ip_cfg.vprint(f"Successfully generated PyMTL wrapper {wrapper_name}!", 2)
    return symbols

  #-----------------------------------------------------------------------
  # import_component
  #-----------------------------------------------------------------------
  # Return the PyMTL component imported from `wrapper_name`.v.

  def import_component( s, m, ph_cfg, ip_cfg, symbols ):
    ip_cfg.vprint("=====Create python object=====")

    component_name = ip_cfg.translated_top_module
    # Get the name of the wrapper Python module
    wrapper_name = ip_cfg.get_py_wrapper_path()
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
      raise VerilogImportError(m,
          f"internal error: PyMTL wrapper {wrapper_name} does not have "
          f"top component {component_name}!") from e

    imp = imp_class()
    ip_cfg.vprint(f"Successfully created python object of {component_name}!", 2)

    # Update the global namespace of `construct` so that the struct and interface
    # classes defined previously can still be used in the imported model.
    imp.construct.__globals__.update( symbols )

    ip_cfg.vprint("Import succeeds!")
    return imp

  #-------------------------------------------------------------------------
  # Serialize and compare configurations
  #-------------------------------------------------------------------------

  def serialize_cfg( s, ip_cfg ):
    d = {}
    s._volatile_configs = [
      'verilog_hash',
      'vl_line_trace', 'vl_coverage', 'vl_line_coverage', 'vl_toggle_coverage',
      'vl_mk_dir', 'vl_enable_assert',
      'vl_W_lint', 'vl_W_style', 'vl_W_fatal', 'vl_Wno_list',
      'vl_xinit', 'vl_trace',
      'vl_trace_timescale', 'vl_trace_cycle_time',
      'c_flags', 'c_include_path', 'c_srcs',
      'ld_flags', 'ld_libs',
    ]
    d['ImportPassName'] = 'VerilogVerilatorImportPass'
    for cfg in s._volatile_configs:
      d[cfg] = copy.deepcopy(getattr( ip_cfg, cfg ))

    return d

  def is_same_cfg( s, prev, new ):
    _volatile_configs = copy.copy(s._volatile_configs)
    _volatile_configs.append('ImportPassName')
    if not all(cfg in prev and cfg in new for cfg in _volatile_configs):
      return False
    return all(prev[cfg] == new[cfg] for cfg in _volatile_configs)

  #-------------------------------------------------------------------------
  # gen_signal_decl_c
  #-------------------------------------------------------------------------
  # Return C variable declaration of `port`.

  def gen_signal_decl_c( s, name, port ):

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
  # Return C port variable initialization.

  def gen_signal_init_c( s, name, port ):

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

  #-------------------------------------------------------------------------
  # gen_signal_decl_py
  #-------------------------------------------------------------------------
  # Return the PyMTL definition of all interface ports of `rtype`.

  def gen_signal_decl_py( s, rtype ):

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
          # Support common python types and Bits/BitStruct

          if isinstance( obj, (int, bool, str) ):
            return str(obj)

          elif obj is None:
            return 'None'

          elif isinstance( obj, type ) and issubclass( obj, Bits ):
            nbits = obj.nbits
            Bits_name = f"Bits{nbits}"
            if Bits_name not in symbols and nbits >= 256:
              Bits_class = mk_bits( nbits )
              symbols.update( { Bits_name : Bits_class } )
            return Bits_name

          elif isinstance( obj, Bits ):
            nbits = obj.nbits
            value = int(obj)
            Bits_name = f"Bits{nbits}"
            Bits_arg_str = f"{Bits_name}( {value} )"
            if Bits_name not in symbols and nbits >= 256:
              Bits_class = mk_bits( nbits )
              symbols.update( { Bits_name : Bits_class } )
            return Bits_arg_str

          elif is_bitstruct_class(obj):
            # Shunning: get the unique name of bitstruct class
            BitStruct_name = _get_rtlir_dtype_struct( obj() ).get_name()

            if BitStruct_name in symbols:
              assert symbols[BitStruct_name] is obj, "Same bitstruct name but different classes!"
            else:
              symbols.update( { BitStruct_name : obj } )

            return BitStruct_name

          # FIXME formalize this
          elif isinstance( obj, type ) and hasattr( obj, 'req' ) and hasattr( obj, 'resp' ):
            symbols.update( { obj.__name__ : obj } )
            return obj.__name__

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

          raise TypeError( f"Interface constructor argument {obj} is not an int/Bits/BitStruct/TypeTuple!" )

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

    return {**p_symbols, **i_symbols}, p_decls + i_decls

  #-----------------------------------------------------------------------
  # Methods that generate python signal writes
  #-----------------------------------------------------------------------

  def _gen_vector_write( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    l, r = pos, pos+nbits
    if d == 'i':
      ret = [ f"{rhs}[{l}:{r}] @= {lhs}" ]
    else:
      ret = [ f"{lhs} @= {rhs}[{l}:{r}]" ]
    return ret, r

  def _gen_struct_write( s, d, lhs, rhs, dtype, pos ):
    ret = []
    all_properties = reversed(list(dtype.get_all_properties().items()))
    for name, field in all_properties:
      _ret, pos = s._gen_write_dispatch( d, f"{lhs}.{name}", rhs, field, pos )
      ret.extend( _ret )
    return ret, pos

  def _gen_packed_array_write( s, d, lhs, rhs, dtype, n_dim, pos ):
    if not n_dim:
      return s._gen_write_dispatch( d, lhs, rhs, dtype, pos )
    # Recursively generate array
    ret = []
    for idx in range(n_dim[0]):
      _ret, pos = s._gen_packed_array_write( d, f"{lhs}[{idx}]", rhs, dtype, n_dim[1:], pos )
      ret.extend( _ret )
    return ret, pos

  def _gen_write_dispatch( s, d, lhs, rhs, dtype, pos ):
    if isinstance( dtype, rdt.Vector ):
      return s._gen_vector_write( d, lhs, rhs, dtype, pos )
    elif isinstance( dtype, rdt.Struct ):
      return s._gen_struct_write( d, lhs, rhs, dtype, pos )
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return s._gen_packed_array_write( d, lhs, rhs, sub_dtype, n_dim, pos )
    assert False, f"unrecognized data type {dtype}!"

  #-------------------------------------------------------------------------
  # gen_comb_input
  #-------------------------------------------------------------------------

  def gen_port_vector_input( s, lhs, rhs, mangled_rhs, dtype, symbols ):
    dtype_nbits = dtype.get_length()
    blocks   = [ '',
                 f's.{mangled_rhs} = Wire( {s._gen_bits_decl(dtype_nbits)} )',
                 '@update',
                 f'def isignal_{mangled_rhs}():',
                 f'  s.{mangled_rhs} @= {rhs}' ]
    set_comb = ( s._gen_ref_write( lhs, 's.'+mangled_rhs, dtype_nbits ) )
    return set_comb, blocks

  def gen_port_struct_input( s, lhs, rhs, mangled_rhs, dtype, symbols ):
    dtype_nbits = dtype.get_length()
    # If the top-level signal is a struct, we add the datatype to symbol?
    dtype_name = dtype.get_class().__name__
    if dtype_name not in symbols:
      symbols[dtype_name] = dtype.get_class()

    blocks   = [ '',
                 f's.{mangled_rhs} = Wire( {s._gen_bits_decl(dtype_nbits)} )',
                 '@update',
                 f'def istruct_{mangled_rhs}():',
                 f'  s.{mangled_rhs} @= {rhs}' ]

    # We don't create a new struct if we are copying values from pymtl
    # land to verilator, i.e. this port is the input to the imported
    # component.
    # At the end, we write tmp to the corresponding CFFI variable
    set_comb = s._gen_ref_write( lhs, 's.'+mangled_rhs, dtype_nbits )
    return set_comb, blocks

  def gen_port_input( s, lhs, rhs, pnames, dtype, symbols ):
    rhs = rhs.format(next(pnames))

    # We always name mangle now
    mangled_rhs = s._pymtl_name_mangle( rhs )

    if isinstance( dtype, rdt.Vector ):
      return s.gen_port_vector_input( lhs, rhs, mangled_rhs, dtype, symbols )

    elif isinstance( dtype, rdt.Struct ):
      return s.gen_port_struct_input( lhs, rhs, mangled_rhs, dtype, symbols )

    else:
      assert False, f"unrecognized data type {dtype}!"

  def gen_port_array_input( s, lhs, rhs, pnames, dtype, index, n_dim, symbols ):
    if not n_dim:
      return s.gen_port_input( lhs, rhs, pnames, dtype, symbols )
    else:
      set_comb, structs = [], []
      for idx in range( n_dim[0] ):
        _lhs = f"{lhs}[{idx}]"
        if index == 0:
          _rhs = f"{rhs}[{idx}]"
          _index = index
        else:
          _rhs = f"{rhs}"
          _index = index-1
        _set_comb, _structs = s.gen_port_array_input( _lhs, _rhs, pnames, dtype, _index, n_dim[1:], symbols )
        set_comb += _set_comb
        structs  += _structs
      return set_comb, structs

  def gen_comb_input( s, packed_ports, symbols ):
    set_comb, structs = [], []
    # Read all input ports ( except for 'clk' ) from component ports into
    # the verilated model. We do NOT want `clk` signal to be read into
    # the verilated model because only the sequential update block of
    # the imported component should manipulate it.

    for _pnames, vname, rtype, port_idx in packed_ports:
      if isinstance( rtype, rt.Array ):
        n_dim = rtype.get_dim_sizes()
      else:
        n_dim = []
      repeats = reduce(lambda a, b: a*b, n_dim[port_idx:], 1)
      pnames = [name for name in _pnames for _ in range(repeats)]
      pnames_iter = cycle(pnames)
      p_n_dim, p_rtype = get_rtype( rtype )
      if s._get_direction( p_rtype ) == 'InPort' and pnames[0] != 'clk' and vname:
        dtype = p_rtype.get_dtype()
        lhs = "_ffi_m."+s._verilator_name(vname)
        rhs = "s.{}"
        idx = port_idx
        _set_comb, _structs = s.gen_port_array_input( lhs, rhs, pnames_iter, dtype, idx, p_n_dim, symbols )
        set_comb += _set_comb
        structs  += _structs

    return set_comb, structs

  #-------------------------------------------------------------------------
  # gen_comb_output
  #-------------------------------------------------------------------------

  def gen_port_vector_output( s, lhs, mangled_lhs, rhs, dtype, symbols ):
    dtype_nbits = dtype.get_length()
    blocks   = [ '',
                 f's.{mangled_lhs} = Wire( {s._gen_bits_decl(dtype_nbits)} )',
                 '@update',
                 f'def osignal_{mangled_lhs}():',
                 f'  {lhs} @= s.{mangled_lhs}' ]

    set_comb = s._gen_ref_read( 's.'+mangled_lhs, rhs, dtype_nbits, '@=' )
    return set_comb, blocks

  def gen_port_struct_output( s, lhs, mangled_lhs, rhs, dtype, symbols ):
    dtype_nbits = dtype.get_length()
    # If the top-level signal is a struct, we add the datatype to symbol?
    dtype_name = dtype.get_name()
    if dtype_name not in symbols:
      symbols[dtype_name] = dtype.get_class()

    blocks   = [ '',
                 f's.{mangled_lhs} = Wire( {s._gen_bits_decl(dtype_nbits)} )',
                 '@update',
                 f'def ostruct_{mangled_lhs}():' ]

    # We create a long Bits object to accept CFFI value for struct
    # the temporary wire name

    # We create a new struct if we are copying values from verilator
    # world to pymtl land and send it out through the output of this
    # component
    body, pos = s._gen_struct_write( 'o', lhs, 's.'+mangled_lhs, dtype, 0 )
    assert pos == dtype.get_length()

    upblk_content = body
    make_indent( upblk_content, 1 )

    blocks += upblk_content

    # We create a long Bits object tmp first
    # Then we load the full Bits to tmp
    set_comb = s._gen_ref_read( 's.'+mangled_lhs, rhs, dtype_nbits, '@=' )
    return set_comb, blocks

  def gen_port_output( s, lhs, pnames, rhs, dtype, symbols ):
    lhs = lhs.format(next(pnames))

    mangled_lhs = s._pymtl_name_mangle( lhs )

    if isinstance( dtype, rdt.Vector ):
      return s.gen_port_vector_output( lhs, mangled_lhs, rhs, dtype, symbols )
    elif isinstance( dtype, rdt.Struct ):
      return s.gen_port_struct_output( lhs, mangled_lhs, rhs, dtype, symbols )
    else:
      assert False, f"unrecognized data type {dtype}!"

  def gen_port_array_output( s, lhs, pnames, rhs, dtype, index, n_dim, symbols ):
    if not n_dim:
      return s.gen_port_output( lhs, pnames, rhs, dtype, symbols )
    else:
      set_comb, structs = [], []
      for idx in range( n_dim[0] ):
        if index == 0:
          _lhs = f"{lhs}[{idx}]"
          _index = index
        else:
          _lhs = f"{lhs}"
          _index = index-1
        _rhs = f"{rhs}[{idx}]"
        _set_comb, _structs = s.gen_port_array_output( _lhs, pnames, _rhs, dtype, _index, n_dim[1:], symbols )
        set_comb += _set_comb
        structs  += _structs
      return set_comb, structs

  def gen_comb_output( s, packed_ports, symbols ):
    set_comb, structs = [], []
    for _pnames, vname, rtype, port_idx in packed_ports:
      if isinstance( rtype, rt.Array ):
        n_dim = rtype.get_dim_sizes()
      else:
        n_dim = []
      repeats = reduce(lambda a, b: a*b, n_dim[port_idx:], 1)
      pnames = [name for name in _pnames for _ in range(repeats)]
      pnames_iter = cycle(pnames)
      p_n_dim, p_rtype = get_rtype( rtype )
      if s._get_direction( rtype ) == 'OutPort':
        dtype = p_rtype.get_dtype()
        lhs = "s.{}"
        rhs = "_ffi_m." + s._verilator_name(vname)
        idx = port_idx
        _set_comb, _structs = s.gen_port_array_output( lhs, pnames_iter, rhs, dtype, idx, p_n_dim, symbols )
        set_comb += _set_comb
        structs  += _structs
    return set_comb, structs

  #-------------------------------------------------------------------------
  # gen_line_trace_py
  #-------------------------------------------------------------------------
  # Return the line trace method body that shows all interface ports.

  def gen_line_trace_py( s, packed_ports ):
    template = '{0}={{s.{0}}},'
    trace_string = ''
    for pnames, _, _, _ in packed_ports:
      for pname in pnames:
        trace_string += ' ' + template.format( pname )
    return f"      return f'{trace_string}'"

  #-------------------------------------------------------------------------
  # gen_internal_line_trace_py
  #-------------------------------------------------------------------------
  # Return the line trace method body that shows all CFFI ports.
  # Now that there could be multiple pnames that correspond to one vname,
  # I'm not sure how to generate internal line trace... maybe we should
  # deprecate internal_line_trace since it's not used by many anyways?

  def gen_internal_line_trace_py( s, packed_ports ):
    # ret = [ '_ffi_m = s._ffi_m', 'lt = ""' ]
    # template = \
    #   "lt += '{vname} = {{}}, '.format(full_vector(s.{pname}, _ffi_m.{vname}))"
    # for pname, vname, port in packed_ports:
    #   if vname:
    #     pname = s._verilator_name(pname)
    #     vname = s._verilator_name(vname)
    #     ret.append( template.format(**locals()) )
    # ret.append( 'return lt' )
    # make_indent( ret, 2 )
    # return '\n'.join( ret )
    return "    return ''"

  #=========================================================================
  # Helper functions
  #=========================================================================

  def _verilator_name( s, name ):
    # TODO: PyMTL translation should generate dollar-sign-free Verilog source
    # code. Verify that this replacement rule here is not necessary.
    return name.replace('__', '___05F').replace('$', '__024')

  def _pymtl_name_mangle( s, name ):
    return name.replace('.', '_DOT_').replace('[', '_LB_').replace(']', '_RB_')

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

  def _gen_ref_write( s, lhs, rhs, nbits, equal='=' ):
    if nbits <= 64:
      return [ '', f"{lhs}[0] {equal} int({rhs})" ]
    else:
      ret = [ '', f'x = {lhs}' ]
      ITEM_BITWIDTH = 32
      num_assigns = (nbits-1)//ITEM_BITWIDTH+1
      for idx in range(num_assigns):
        l = ITEM_BITWIDTH*idx
        r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
        ret.append( f"x[{idx}] {equal} int({rhs}[{l}:{r}])" )
      return ret

  def _gen_ref_read( s, lhs, rhs, nbits, equal='=' ):
    if nbits <= 64:
      return [ '', f"{lhs} {equal} {rhs}[0]" ]
    else:
      ret = [ '', f'x = {rhs}' ]
      ITEM_BITWIDTH = 32
      num_assigns = (nbits-1)//ITEM_BITWIDTH+1
      for idx in range(num_assigns):
        l = ITEM_BITWIDTH*idx
        r = l+ITEM_BITWIDTH if l+ITEM_BITWIDTH <= nbits else nbits
        _nbits = r - l
        ret.append( f"{lhs}[{l}:{r}] @= x[{idx}]" )
      return ret

  def _gen_bits_decl( s, nbits ):
    if nbits < 256:
      return f'Bits{nbits}'
    else:
      return f'mk_bits({nbits})'
