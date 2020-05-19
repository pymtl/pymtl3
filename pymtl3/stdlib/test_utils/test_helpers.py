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
from pymtl3.passes.backends.verilog import *

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

    self.model.apply( DefaultPassGroup(print_line_trace=True) )

    self.model.sim_reset()

    for test_vector in self.test_vectors:

      # Set inputs
      self.set_inputs_func( self.model, test_vector )

      self.model.sim_eval_combinational()

      try:
        # Verify outputs
        self.verify_outputs_func( self.model, test_vector )
      except Exception as e:
        self.model.print_line_trace()
        raise e

      self.model.sim_tick()

def run_sim( model, dump_vcd=None, test_verilog=False, line_trace=True, max_cycles=5000 ):

  # Setup the model

  model.elaborate()

  if dump_vcd:
    model.set_metadata( VcdGenerationPass.vcd_file_name, dump_vcd )

  if test_verilog:
    model.set_metadata( VerilogVerilatorImportPass.vl_xinit, test_verilog )
    model.set_metadata( VerilogTranslationImportPass.enable, True )

  model.apply( VerilogPlaceholderPass() )
  model = VerilogTranslationImportPass()( model )

  # Create a simulator

  model.apply( DefaultPassGroup(print_line_trace=line_trace) )

  # Reset model

  model.sim_reset()

  # Run simulation

  while not model.done() and model.sim_cycle_count() < max_cycles:
    model.sim_tick()

  # Force a test failure if we timed out

  assert model.sim_cycle_count() < max_cycles

  # Extra ticks to make VCD easier to read

  model.sim_tick()
  model.sim_tick()
  model.sim_tick()

class RunTestVectorSimError( Exception ):
  pass

def run_test_vector_sim( model, test_vectors, cmdline_opts=None, line_trace=True ):
  cmdline_opts = cmdline_opts or {'dump_vcd': False, 'test_verilog': False}

  # First row in test vectors contains port names

  if isinstance(test_vectors[0],str):
    port_names = test_vectors[0].split()
  else:
    port_names = test_vectors[0]

  # Remaining rows contain the actual test vectors

  test_vectors = test_vectors[1:]

  # Setup the model

  model.elaborate()

  if cmdline_opts['dump_vcd']:
    model.set_metadata( VcdGenerationPass.vcd_file_name, cmdline_opts['dump_vcd'] )

  if cmdline_opts['test_verilog']:
    model.set_metadata( VerilogVerilatorImportPass.vl_xinit, cmdline_opts['test_verilog'] )
    model.set_metadata( VerilogTranslationImportPass.enable, True )

  model.apply( VerilogPlaceholderPass() )
  model = VerilogTranslationImportPass()( model )

  # Create a simulator

  model.apply( DefaultPassGroup(print_line_trace=True) )

  # Reset model

  model.sim_reset()

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
      x = getattr( model, g[1] )
      if g[0]:
        x[g[2]] @= in_value
      else:
        x @= in_value

    # Evaluate combinational concurrent blocks

    model.sim_eval_combinational()

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
        if line_trace:
          model.print_line_trace()

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

    model.sim_tick()

  # Extra ticks to make VCD easier to read

  model.sim_tick()
  model.sim_tick()
  model.sim_tick()
