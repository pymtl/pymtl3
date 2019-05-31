#=========================================================================
# ImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 25, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""

from __future__ import absolute_import, division, print_function

import copy
import importlib
import os
import shutil
import subprocess

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.sverilog.errors import SVerilogImportError
from pymtl3.passes.sverilog.utility import get_component_unique_name, make_indent

from .helpers import (
    gen_all_ports,
    gen_comb_input,
    gen_comb_output,
    gen_internal_line_trace_py,
    gen_line_trace_py,
    gen_seq_output,
    gen_signal_decl_c,
    gen_signal_decl_py,
    gen_signal_init_c,
)


class ImportPass( BasePass ):
  """Import an arbitrary SystemVerilog module as a PyMTL component.
  
  The import pass takes as input a PyMTL component hierarchy where
  the components to be imported have an `import` entry in their parameter
  dictionary( set by calling the `set_parameter` PyMTL API ).
  This pass assumes the modules to be imported are located in the current
  directory and have name {module_name}.sv where `module_name` is the name of
  component's class. The top module inside the target .sv file should
  have a full name which is has the following format:
      > {module_name}[__{parameter_name}_{parameter_value}]*
  As an example, component mux created through `mux = Mux(Bits32, 2)` has a
  full name `Mux__Type_Bits32__ninputs_2`.
  """
  def __call__( s, top ):
    s.traverse_hierarchy( top )

  def traverse_hierarchy( s, m ):
    try:
      if m._pass_sverilog_import.import_:
        s.do_import( m )
    except AttributeError:
      for child in m.get_child_components():
        s.traverse_hierarchy( child )

  def do_import( s, m ):
    rtype = get_component_ifc_rtlir( m )
    name = rtype.get_name()
    full_name = get_component_unique_name( rtype )
    all_ports = gen_all_ports( m, rtype )
    try:
      create_verilator_model( name, full_name )

      c_wrapper_name, port_cdefs = \
          create_verilator_c_wrapper( name, full_name, all_ports )

      lib_name = \
          create_shared_lib( c_wrapper_name, name )

      py_wrapper_name = \
          create_py_wrapper( name, all_ports, lib_name, port_cdefs )

      imported_obj = import_component( py_wrapper_name, name )

      swap_in_imported_component( m, imported_obj, all_ports )
    except AssertionError as e:
      msg = '' if e.args[0] is None else e.args[0]
      raise SVerilogImportError( m, msg )

  def get_component_obj( s, name ):
    pass

  def connect_imported_obj( s, m, obj, rtype ):
    pass

#-----------------------------------------------------------------------
# create_verilator_model
#-----------------------------------------------------------------------

def create_verilator_model( file_name, top_name ):
  """Verilate module `top_name` in `file_name`.sv."""
  obj_dir = 'obj_dir_' + file_name
  flags = ' '.join( [
    '--unroll-count 1000000', '--unroll-stmts 1000000', '--assert',
    '-Wno-UNOPTFLAT', '-Wno-UNSIGNED', ] )
  cmd = \
"""\
verilator -cc {file_name} -top-module {top_name} --Mdir {obj_dir} -O3 {flags}
"""
  cmd = cmd.format( **locals() )

  # Remove obj_dir directory if it already exists.
  # obj_dir is where the verilator output ( C headers and sources ) is stored
  if os.path.exists( obj_dir ):
    shutil.rmtree( obj_dir )

  # Print out the modification time stamp of SystemVerilog source file
  # print 'Modification timestamp of {}.sv: {}'.format(
      # file_name, os.path.getmtime( file_name + '.sv' ) )

  # Try to call verilator
  try:
    subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True )
  except subprocess.CalledProcessError as e:
    assert False, \
"""\
Fail to verilate model {} in file {}.sv
  Verilator command:
  {}

  Verilator output:
  {}
""".format( top_name, file_name, cmd, e.output )

#-----------------------------------------------------------------------
# create_verilator_c_wrapper
#-----------------------------------------------------------------------

def create_verilator_c_wrapper( file_name, all_ports ):
  """Return the file name of generated C component wrapper.
  
  Create a C wrapper that calls verilator C API and provides interfaces
  that can be later called through CFFI.
  """
  component_name = file_name

  # The wrapper template should be in the same directory as this file
  template_name = \
    os.path.dirname( os.path.abspath( __file__ ) ) + \
    os.path.sep + 'verilator_wrapper.template.c'

  wrapper_name = file_name + '_v.cpp'

  # Generate port declarations for the verilated model in C
  port_defs = []
  for name, port, _ in all_ports:
    port_defs.append( gen_signal_decl_c( name, port ) )
  port_cdefs = copy.copy( port_defs )
  make_indent( port_defs, 2 )
  port_defs = '\n'.join( port_defs )

  # Generate initialization statements for in/out ports
  port_inits = []
  for name, port, _ in all_ports:
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

def create_shared_lib( wrapper_name, file_name ):
  """Return the name of compiled shared lib."""
  lib_name = 'lib{}_v.so'.format( file_name )

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
  obj_dir_prefix = 'obj_dir_{}/V{}'.format( file_name, file_name )
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
          cpp_file = 'obj_dir_{}/{}.cpp'.format( file_name, cpp_file_name )
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

def create_py_wrapper( name, all_ports, lib_file, port_cdefs ):
  """Return the file name of the generated PyMTL component wrapper."""

  # Load the wrapper template
  template_name = \
    os.path.dirname( os.path.abspath( __file__ ) ) + \
    os.path.sep + 'verilator_wrapper.template.py'
  wrapper_name = name + '_v.py'

  # Port definitions of verilated model
  make_indent( port_cdefs, 4 )

  # Port definition in PyMTL style
  port_defs = []
  for name, port, _ in all_ports:
    port_defs.append( gen_signal_decl_py( name, port ) )
  make_indent( port_defs, 2 )

  # Set upblk inputs and outputs
  set_comb_input = gen_comb_input( all_ports )
  set_comb_output = gen_comb_output( all_ports )
  set_seq_output = gen_seq_output( all_ports )
  make_indent( set_comb_input, 3 )
  make_indent( set_comb_output, 3 )
  make_indent( set_seq_output, 3 )

  # Line trace 
  line_trace = gen_line_trace_py( all_ports )

  # Internal line trace 
  in_line_trace = gen_internal_line_trace_py( all_ports )

  # Fill in the python wrapper template
  with open( template_name, 'r' ) as template:
    with open( wrapper_name, 'w' ) as output:
      py_wrapper = template.read()
      py_wrapper = py_wrapper.format(
        component_name  = name,
        lib_file        = lib_file,
        port_cdefs      = ('  '*4+'\n').join( port_cdefs ),
        port_defs       = '\n'.join( port_defs ),
        set_comb_input  = '\n'.join( set_comb_input ),
        set_comb_output = '\n'.join( set_comb_output ),
        set_seq_output  = '\n'.join( set_seq_output ),
        line_trace      = line_trace,
        in_line_trace   = in_line_trace,
      )
      output.write( py_wrapper )

  return wrapper_name

#-----------------------------------------------------------------------
# import_component
#-----------------------------------------------------------------------

def import_component( wrapper_name, component_name ):
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
    imp = getattr(sys.modules[wrapper], component_name)
  except AttributeError:
    assert False, \
      "internal error: PyMTL wrapper {} does not have top component {}!". \
        format( wrapper_name, component_name )
  return imp()

#-----------------------------------------------------------------------
# swap_in_imported_component
#-----------------------------------------------------------------------

def swap_in_imported_component( m, imp, all_ports ):
  pass
