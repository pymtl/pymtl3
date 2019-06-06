#=========================================================================
# test_utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Provide utility methods for testing."""

from __future__ import absolute_import, division, print_function

from pymtl3.dsl import OutPort
from pymtl3.passes.sverilog import ImportPass, TranslationPass
from pymtl3.stdlib.test import TestVectorSimulator

#-------------------------------------------------------------------------
# closed_loop_component_input_test
#-------------------------------------------------------------------------

def closed_loop_component_input_test( dut, test_vector, tv_in ):

  # Filter to collect all interface ports of a component
  def interface_port_filter( obj ):
    return isinstance( obj, OutPort )

  reference_output = []
  all_output_ports = dut.get_all_object_filter( interface_port_filter )

  # Method to record reference outputs of the pure python component
  def ref_tv_out( model, test_vector ):
    dct = {}
    for out_port in all_output_ports:
      dct[ out_port ] = getattr( model, out_port.my_name )
    reference_output.append( dct )

  # Method to compare the outputs of the imported model and the pure python one
  def tv_out( model, test_vector ):
    assert reference_output, \
      "Reference runs for fewer cycles than the imported model!"
    for out_port in all_output_ports:
      ref = reference_output[0][out_port]
      imp = getattr( model, out_port.my_name )
      assert ref == imp, \
        "Value mismatch: reference: {}, imported: {}".format( ref, imp )

  # First simulate the pure python component to see if it has sane behavior
  reference_sim = TestVectorSimulator( dut, test_vector, tv_in, ref_tv_out )
  reference_sim.run_test()
  dut.unlock_simulation()

  # If it simulates correctly, translate it and import it back
  try:
    dut.elaborate()
    dut._sverilog_translate = True
    dut._sverilog_import = True
    dut.apply( TranslationPass() )
    imported_obj = ImportPass()( dut )
    imported_sim = TestVectorSimulator( imported_obj, test_vector, tv_in, tv_out )
    imported_sim.run_test()
  finally:
    try:
      # Explicitly finalize the imported object because the shared lib may have
      # name collison
      imported_obj.finalize()
    except UnboundLocalError:
      pass

#-------------------------------------------------------------------------
# closed_loop_component_test
#-------------------------------------------------------------------------

def closed_loop_component_test( dut ):
  pass

#-------------------------------------------------------------------------
# closed_loop_test
#-------------------------------------------------------------------------

def closed_loop_test():
  pass
