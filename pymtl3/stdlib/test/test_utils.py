"""
========================================================================
test_utils
========================================================================
Helper functions for running unit tests

Author : Shunning Jiang
  Date : Jan 23, 2020
"""

import collections
import re

from pymtl3 import *
from pymtl3.datatypes import is_bitstruct_class
from pymtl3.passes import TracingConfigs
from pymtl3.passes.backends.sverilog import (
    TranslationImportPass,
    VerilatorImportConfigs,
    VerilatorImportPass,
    VerilogPlaceholderPass,
)

#-------------------------------------------------------------------------
# config_model
#-------------------------------------------------------------------------

def config_model( m, dump_vcd, test_verilog, duts = [] ):

  def traverse_translate_import( module ):
    if isinstance( module, Placeholder ):
      module.sverilog_translate_import = True
    else:
      for child in module.get_child_components():
        traverse_translate_import( child )

  def traverse_import_vl_trace( module ):
    if isinstance( module, Placeholder ):
      if not hasattr( module, 'config_sverilog_import' ):
        module.config_sverilog_import = VerilatorImportConfigs()
      module.config_sverilog_import.vl_trace = True
    else:
      for child in module.get_child_components():
        traverse_import_vl_trace( child )

  m.elaborate()

  # For each placeholder in the hierarchy, set them as to be translated
  # and imported
  traverse_translate_import( m )

  if not duts:
    duts.append( '' )

  # Set --dump-vcd and --test-verilog related configs
  for dut_attr in duts:
    if dut_attr == '':
      dut = m
    else:
      dut = eval(f'm.{dut_attr}')

    # If --test-verilog is on, tag the target module
    if test_verilog:
      dut.sverilog_translate_import = True

    if dump_vcd:
      # Use PyMTL VCD tracing if --test-verilog is off and there is at
      # least one PyMTL component
      if not isinstance( dut, Placeholder ) and not test_verilog:
        m.config_tracing = TracingConfigs( tracing='vcd', vcd_file_name=dump_vcd )
        # We also need to mark every placeholder in the hierarchy to 
        # use Verilator tracing
        traverse_import_vl_trace( m )
      # Otherwise use Verilator VCD tracing
      else:
        if not hasattr( dut, 'config_sverilog_import' ):
          dut.config_sverilog_import = VerilatorImportConfigs()
        dut.config_sverilog_import.vl_trace = True

#-------------------------------------------------------------------------
# mk_test_case_table
#-------------------------------------------------------------------------

def mk_test_case_table( raw_test_case_table ):

  # First row in test vectors contains port names

  if isinstance(raw_test_case_table[0],str):
    test_param_names = raw_test_case_table[0].split()
  else:
    test_param_names = raw_test_case_table[0]

  TestCase = collections.namedtuple("TestCase",test_param_names)

  ids = []
  test_cases = []
  for row in raw_test_case_table[1:]:
    ids.append( row[0] )
    test_cases.append( TestCase(*row[1:]) )

  return {
    'ids'      : ids,
    'argnames' : ('test_params'),
    'argvalues' : test_cases,
  }

#------------------------------------------------------------------------------
# TestVectorSimulator
#------------------------------------------------------------------------------
# Now we have the same test vector simulator as pymtl2
# https://github.com/cornell-brg/pymtl/blob/master/pclib/test/TestVectorSimulator.py

class TestVectorSimulator:

  def __init__( self, model, test_vectors,
                set_inputs_func, verify_outputs_func, wait_cycles = 0 ):

    self.model               = model
    self.set_inputs_func     = set_inputs_func
    self.verify_outputs_func = verify_outputs_func
    self.test_vectors        = test_vectors
    self.wait_cycles         = wait_cycles

  def run_test( self ):

    self.model.apply( SimulationPass() )

    self.model.sim_reset()

    print()
    for test_vector in self.test_vectors:

      # Set inputs
      self.set_inputs_func( self.model, test_vector )

      self.model.eval_combinational()

      # Print the line trace
      print(self.model.line_trace())

      # Verify outputs
      self.verify_outputs_func( self.model, test_vector )

      self.model.tick()

def run_sim( model, dump_vcd=None, test_verilog=False, line_trace=True, max_cycles=5000 ):

  # Setup the model

  model.elaborate()

  # if dump_vcd:
  #   if not isinstance( model, Placeholder ) and not test_verilog:
  #     model.config_tracing = TracingConfigs( tracing='vcd', vcd_file_name=dump_vcd )
  #   else:
  #     _set_config(
  #       model, 'config_sverilog_import', VerilatorImportConfigs(),
  #       'vl_trace', True, )

  # if test_verilog:
  #   model.sverilog_translate_import = True
  #   _set_config(
  #       model, 'config_sverilog_import', VerilatorImportConfigs(),
  #       'vl_xinit', test_verilog )

  model.apply( VerilogPlaceholderPass() )
  model = TranslationImportPass()( model )

  # Create a simulator

  model.apply( SimulationPass() )

  # Reset model

  model.sim_reset( print_line_trace=line_trace )

  # Run simulation

  while not model.done() and model.simulated_cycles < max_cycles:
    if line_trace:
      model.print_line_trace()
    model.tick()

  # Force a test failure if we timed out

  assert model.simulated_cycles < max_cycles

  # Extra ticks to make VCD easier to read

  model.tick()
  model.tick()
  model.tick()

class RunTestVectorSimError( Exception ):
  pass

def run_test_vector_sim( model, test_vectors, dump_vcd=None, test_verilog=False, line_trace=True ):

  # First row in test vectors contains port names

  if isinstance(test_vectors[0],str):
    port_names = test_vectors[0].split()
  else:
    port_names = test_vectors[0]

  # Remaining rows contain the actual test vectors

  test_vectors = test_vectors[1:]

  # Setup the model

  model.elaborate()

  # NOTE: this needs to be fixed later!
  # Current we only look at the top level component. If it is a
  # place holder, we add the default import config so that is can be
  # imported. Ideally we should have a translation mechanism that
  # generates a pickled source file even if some of them are place 
  # holders to be imported from external Verilog sources.

  if dump_vcd:
    if not isinstance( model, Placeholder ) and not test_verilog:
      model.config_tracing = TracingConfigs( tracing='vcd', vcd_file_name=dump_vcd )
    else:
      _set_config(
        model, 'config_sverilog_import', VerilatorImportConfigs(),
        'vl_trace', True, )

  if test_verilog:
    model.sverilog_translate_import = True
    _set_config(
        model, 'config_sverilog_import', VerilatorImportConfigs(),
        'vl_xinit', test_verilog )

  model.apply( VerilogPlaceholderPass() )
  model = TranslationImportPass()( model )

  # Create a simulator

  model.apply( SimulationPass() )

  # Reset model

  model.sim_reset( print_line_trace=line_trace )

  # Run the simulation

  row_num = 0

  in_ids  = []
  out_ids = []

  groups = [ None ] * len(port_names)
  types  = [ None ] * len(port_names)

  # Preprocess default type
  # Special case for lists of ports
  # NOTE THAT WE ONLY SUPPORT 1D ARRAY and no interface

  for i, port_full_name in enumerate( port_names ):
    if port_full_name[-1] == "*":
      out_ids.append( i )
      port_name = port_full_name[:-1]
    else:
      in_ids.append( i )
      port_name = port_full_name

    if '[' in port_name:

      # Get tokens of the full name

      m = re.match( r'(\w+)\[(\d+)\]', port_name )

      if not m:
        raise Exception(f"Could not parse port name: {port_name}. "
                        f"Currently we don't support interface or high-D array.")

      groups[i] = g = ( True, m.group(1), int(m.group(2)) )

      # Get type of all the ports
      t = type( getattr( model, g[1] )[ int(g[2]) ] )
      types[i] = None if is_bitstruct_class( t ) else t

    else:
      groups[i] = ( False, port_name )
      t = type( getattr( model, port_name ) )
      types[i] = None if is_bitstruct_class( t ) else t

  for row in test_vectors:
    row_num += 1

    # Apply test inputs

    for i in in_ids:

      in_value = row[i]
      t = types[i]
      if t:
        in_value = t( in_value )

      g = groups[i]
      if g[0]:
        getattr( model, g[1] )[g[2]] = in_value
      else:
        setattr( model, g[1], in_value )

    # Evaluate combinational concurrent blocks

    model.eval_combinational()

    # Display line trace output

    if line_trace:
      model.print_line_trace()

    # Check test outputs

    for i in out_ids:
      ref_value = row[i]
      if ref_value == '?':
        continue

      g = groups[i]
      if g[0]:
        out_value = getattr( model, g[1] )[g[2]]
      else:
        out_value = getattr( model, g[1] )

      if out_value != ref_value:

        error_msg = """
run_test_vector_sim received an incorrect value!
- row number     : {row_number}
- port name      : {port_name}
- expected value : {expected_msg}
- actual value   : {actual_msg}
"""
        raise RunTestVectorSimError( error_msg.format(
          row_number   = row_num,
          port_name    = port_name,
          expected_msg = ref_value,
          actual_msg   = out_value
        ))

    # Tick the simulation

    model.tick()

  # Extra ticks to make VCD easier to read

  model.tick()
  model.tick()
  model.tick()

  # NOTE: this will destory the imported component!
  try:
    model.finalize()
  except:
    pass

#-------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------

def _set_config( m, config_attr, default_config, config, value ):
  if not hasattr( m, config_attr ):
    setattr( m, config_attr, default_config )
  setattr( getattr( m, config_attr ), config, value )
