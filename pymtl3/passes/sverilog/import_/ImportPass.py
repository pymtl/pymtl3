#=========================================================================
# ImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 25, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""

from __future__ import absolute_import, division, print_function

import copy
import importlib
import linecache
import os
import shutil
import subprocess
import sys

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.sverilog.errors import SVerilogImportError
from pymtl3.passes.sverilog.util.utility import get_component_unique_name, make_indent

from .helpers import (
    gen_comb_input,
    gen_comb_output,
    gen_internal_line_trace_py,
    gen_line_trace_py,
    gen_packed_ports,
    gen_signal_decl_c,
    gen_signal_decl_py,
    gen_signal_init_c,
    gen_wire_decl_py,
)


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
        "please elaborate design {} before applying the import pass!". \
          format(top) )
    ret = s.traverse_hierarchy( top )
    if ret is None:
      ret = top
    return ret

  def traverse_hierarchy( s, m ):
    try:
      if m._sverilog_import:
        return s.do_import( m )
    except AttributeError:
      pass
    finally:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

  def do_import( s, m ):
    try:
      imp = get_imported_object( m )
      if m is s.top:
        return imp
      else:
        s.top.replace_component_with_obj( m, imp )
    except AssertionError as e:
      msg = '' if e.args[0] is None else e.args[0]
      raise SVerilogImportError( m, msg )

#-----------------------------------------------------------------------
# get_imported_object
#-----------------------------------------------------------------------

def get_imported_object( m ):
  rtype = get_component_ifc_rtlir( m )
  full_name = get_component_unique_name( rtype )
  packed_ports = gen_packed_ports( rtype )

  try:
    sv_file_path = m._sverilog_import_path
  except AttributeError:
    sv_file_path = full_name + '.sv'

  assert os.path.isfile( sv_file_path ), \
    "Cannot import {}: {} is not a file!".format( m, sv_file_path )

  create_verilator_model( sv_file_path, full_name )

  c_wrapper_name, port_cdefs = \
      create_verilator_c_wrapper( full_name, packed_ports )

  lib_name = \
      create_shared_lib( c_wrapper_name, full_name )

  py_wrapper_name, symbols = \
      create_py_wrapper( full_name, rtype, packed_ports,
                         lib_name, port_cdefs )

  imp = import_component( py_wrapper_name, full_name, symbols )

  return imp

#-----------------------------------------------------------------------
# create_verilator_model
#-----------------------------------------------------------------------

def create_verilator_model( sv_file_path, top_name ):
  """Verilate module `top_name` in `sv_file_path`."""
  obj_dir = 'obj_dir_' + top_name
  flags = ' '.join( [
    '--unroll-count 1000000', '--unroll-stmts 1000000', '--assert',
    '-Wno-UNOPTFLAT', '-Wno-UNSIGNED', ] )
  cmd = \
"""\
verilator -cc {sv_file_path} -top-module {top_name} --Mdir {obj_dir} -O3 {flags}
"""
  cmd = cmd.format( **locals() )

  # Remove obj_dir directory if it already exists.
  # obj_dir is where the verilator output ( C headers and sources ) is stored
  if os.path.exists( obj_dir ):
    shutil.rmtree( obj_dir )

  # Print out the modification time stamp of SystemVerilog source file
  # print 'Modification timestamp of {}.sv: {}'.format(
      # top_name, os.path.getmtime( top_name + '.sv' ) )

  # Try to call verilator
  try:
    subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True )
  except subprocess.CalledProcessError as e:
    assert False, \
"""\
Fail to verilate model {} in file {}
  Verilator command:
  {}

  Verilator output:
  {}
""".format( top_name, sv_file_path, cmd, e.output )

#-----------------------------------------------------------------------
# create_verilator_c_wrapper
#-----------------------------------------------------------------------

def create_verilator_c_wrapper( full_name, packed_ports ):
  """Return the file name of generated C component wrapper.

  Create a C wrapper that calls verilator C API and provides interfaces
  that can be later called through CFFI.
  """
  component_name = full_name

  # The wrapper template should be in the same directory as this file
  template_name = \
    os.path.dirname( os.path.abspath( __file__ ) ) + \
    os.path.sep + 'verilator_wrapper.c.template'

  wrapper_name = full_name + '_v.cpp'

  # Generate port declarations for the verilated model in C
  port_defs = []
  for name, port in packed_ports:
    port_defs.append( gen_signal_decl_c( name, port ) )
  port_cdefs = copy.copy( port_defs )
  make_indent( port_defs, 2 )
  port_defs = '\n'.join( port_defs )

  # Generate initialization statements for in/out ports
  port_inits = []
  for name, port in packed_ports:
    port_inits.extend( gen_signal_init_c( name, port ) )
  make_indent( port_inits, 1 )
  port_inits = '\n'.join( port_inits )

  # Fill in the C wrapper template
  with open( template_name, 'r' ) as template:
    with open( wrapper_name, 'w' ) as output:
      c_wrapper = template.read()
      c_wrapper = c_wrapper.format( **locals() )
      output.write( c_wrapper )

  return wrapper_name, port_cdefs

#-----------------------------------------------------------------------
# create_shared_lib
#-----------------------------------------------------------------------

def create_shared_lib( wrapper_name, full_name ):
  """Return the name of compiled shared lib."""
  lib_name = 'lib{}_v.so'.format( full_name )

  # Find out the include directory of Verilator
  # First look at $PYMTL_VERILATOR_INCLUDE_DIR environment variable
  verilator_include_dir = os.environ.get( 'PYMTL_VERILATOR_INCLUDE_DIR' )

  # If it is not defined, try to obtain the directory through `pkg-config`
  if verilator_include_dir is None:
    cmd = ['pkg-config', '--variable=includedir', 'verilator']
    try:
      verilator_include_dir = \
        subprocess.check_output( cmd, stderr=subprocess.STDOUT ).strip()
    except OSError:
      assert False, \
"""\
Cannot locate the include directory of verilator. Please make sure either
$PYMTL_VERILATOR_INCLUDE_DIR is set or pkg-config has been configured properly!
"""

  include_dirs = [ verilator_include_dir, verilator_include_dir + '/vltstd' ]
  obj_dir_prefix = 'obj_dir_{}/V{}'.format( full_name, full_name )
  cpp_sources_list = []

  # Read through make file of the verilated model to find the cpp files we need
  with open( obj_dir_prefix + "_classes.mk" ) as makefile:
    found = False
    for line in makefile:
      if line.startswith("VM_CLASSES_FAST += "):
        found = True
      elif found:
        if line.strip() == '':
          found = False
        else:
          cpp_file_name = line.strip()[:-2]
          cpp_file = 'obj_dir_{}/{}.cpp'.format( full_name, cpp_file_name )
          cpp_sources_list.append( cpp_file )

  # Complete the cpp sources file list
  cpp_sources_list += [
    obj_dir_prefix + '__Syms.cpp',
    verilator_include_dir + '/verilated.cpp',
    verilator_include_dir + '/verilated_dpi.cpp',
    wrapper_name,
  ]

  # Call compiler with generated flags & dirs
  cmd = 'g++ {flags} {idirs} -o {ofile} {ifiles}'.format(
    flags  = '-O0 -fPIC -shared',
    idirs  = ' '.join( [ '-I' + d for d in include_dirs ] ),
    ofile  = lib_name,
    ifiles = ' '.join( cpp_sources_list )
  )

  # Print out the modification timestamp of C wrapper
  # print 'Modification timestamp of {}: {}'.format(
      # wrapper_name, os.path.getmtime( wrapper_name ))

  # Try to call the C compiler
  try:
    subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True )
  except subprocess.CalledProcessError as e:
    assert False, \
"""\
Fail to compile Verilated model into a shared library:
  C compiler command:
  {}

  C compiler output:
  {}
""".format( cmd, e.output )

  return lib_name

#-----------------------------------------------------------------------
# create_py_wrapper
#-----------------------------------------------------------------------

def create_py_wrapper( m_name, rtype, packed_ports, lib_file,
                       port_cdefs ):
  """Return the file name of the generated PyMTL component wrapper."""

  # Load the wrapper template
  template_name = \
    os.path.dirname( os.path.abspath( __file__ ) ) + \
    os.path.sep + 'verilator_wrapper.py.template'
  wrapper_name = m_name + '_v.py'

  # Port definitions of verilated model
  make_indent( port_cdefs, 4 )

  # Port definition in PyMTL style
  symbols, port_defs, connections = gen_signal_decl_py( rtype )
  make_indent( port_defs, 2 )
  make_indent( connections, 2 )
  # Wire definition in PyMTL style
  wire_defs = []
  for name, port in packed_ports:
    wire_defs.append( gen_wire_decl_py( name, port ) )
  make_indent( wire_defs, 2 )

  # Set upblk inputs and outputs
  set_comb_input = gen_comb_input( packed_ports )
  set_comb_output = gen_comb_output( packed_ports )
  make_indent( set_comb_input, 3 )
  make_indent( set_comb_output, 3 )

  # Generate constraints for sequential upblk
  # constraints = gen_constraints( all_ports )
  # make_indent( constraints, 3 )
  # constraint_str = ''.join( map( lambda s: "\n"+s, constraints ) )
  # if constraint_str:
    # constraint_str += '\n    '

  # Line trace
  line_trace = gen_line_trace_py( packed_ports )

  # Internal line trace
  in_line_trace = gen_internal_line_trace_py( packed_ports )

  # Fill in the python wrapper template
  with open( template_name, 'r' ) as template:
    with open( wrapper_name, 'w' ) as output:
      py_wrapper = template.read()
      py_wrapper = py_wrapper.format(
        component_name  = m_name,
        lib_file        = lib_file,
        port_cdefs      = ('  '*4+'\n').join( port_cdefs ),
        port_defs       = '\n'.join( port_defs ),
        wire_defs       = '\n'.join( wire_defs ),
        connections     = '\n'.join( connections ),
        set_comb_input  = '\n'.join( set_comb_input ),
        set_comb_output = '\n'.join( set_comb_output ),
        # constraints     = constraint_str,
        line_trace      = line_trace,
        in_line_trace   = in_line_trace,
      )
      output.write( py_wrapper )

  return wrapper_name, symbols

#-----------------------------------------------------------------------
# import_component
#-----------------------------------------------------------------------

def import_component( wrapper_name, component_name, symbols ):
  """Return the PyMTL component imported from `wrapper_name`.sv."""

  # Get the name of the wrapper Python module
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
  except AttributeError:
    assert False, \
      "internal error: PyMTL wrapper {} does not have top component {}!". \
        format( wrapper_name, component_name )

  imp = imp_class()

  # Update the global namespace of `construct` so that the struct and interface
  # classes defined previously can still be used in the imported model.
  imp.construct.__globals__.update( symbols )

  return imp
