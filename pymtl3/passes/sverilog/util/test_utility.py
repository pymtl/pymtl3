#=========================================================================
# test_utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Provide utility methods for testing."""
from __future__ import absolute_import, division, print_function


#-------------------------------------------------------------------------
# closed_loop_component_input_test
#-------------------------------------------------------------------------

def closed_loop_component_input_test( dut, test_vector, tv_in ):

  # Filter to collect all interface ports of a component
  def interface_port_filter( obj ):
    return isinstance( obj, OutPort )

  reference_output = []
  ref_cycles, imp_cycles = 0, 0
  all_output_ports = dut.get_all_object_filter( interface_port_filter )

  # Method to record reference outputs of the pure python component
  def ref_tv_out( model, test_vector ):
    dct = {}
    for out_port in all_output_ports:
      dct[ out_port ] = getattr( model, out_port.my_name )
    reference_output.append( dct )
    ref_cycles += 1

  # Method to compare the outputs of the imported model and the pure python one
  def tv_out( model, test_vector ):
    assert reference_output, \
      "Reference executes for {} cycles but imported model executes {} cycles!". \
        format( ref_cycles, imp_cycles )
    for out_port in all_output_ports:
      ref = reference_output[0][out_port]
      imp = getattr( model, out_port.my_name )
      assert ref == imp, \
        "Value mismatch: reference: {}, imported: {}".format( ref, imp )

  # First simulate the pure python component to see if it has sane behavior
  reference_sim = TestVectorSimulator( dut, test_vector, tv_in, ref_tv_out )
  reference_sim.run_test()

  # If it simulates correctly, translate it and import it back
  dut.apply( TranslationPass() )
  dut._sverilog_import = True
  imported_obj = ImportPass()( dut )
  imported_sim = TestVectorSimulator( imported_obj, test_vector, tv_in, tv_out )
  imported_sim.run_test()

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
