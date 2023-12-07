"""
========================================================================
spec_test_harness.py
========================================================================
Test harnessnes for Verilog specification testing.

Author : Peitian Pan
  Date : Dec 6, 2023
"""

import copy

from pymtl3 import Component, DefaultPassGroup
from pymtl3.passes.backends.verilog import *

class SpecTestHarnessBase: pass

class SpecTestHarnessVector( SpecTestHarnessBase ):
  def __init__( s, dut, input_vector_list_map, apply_input_func=None, check_output_func=None ):
    s.dut = dut
    s.ref = copy.deepcopy(dut)
    s.ref.elaborate()

    s.input_vector_list_map = input_vector_list_map

    if apply_input_func is None:
      s.apply_input_func = s.gen_apply_input_func()
    else:
      s.apply_input_func = apply_input_func

    if check_output_func is None:
      s.check_output_func = s.gen_check_output_func()
    else:
      s.check_output_func = check_output_func

  def gen_apply_input_func( s ):

    def apply_input( model, input_vector_map ):
      for port_name, value in input_vector_map.items():
        port = getattr( model, port_name )
        port @= value

    return apply_input

  def gen_check_output_func( s ):

    def check_output( dut, ref ):
      # Inspect ref component to get a list of output ports to compare.
      # TODO: cache this out_ports list to avoid doing this every cycle.
      out_ports = [ x.get_field_name() for x in ref.get_output_value_ports() ]
      for out_port_name in out_ports:
        dut_value = getattr( dut, out_port_name )
        ref_value = getattr( ref, out_port_name )
        assert dut_value == ref_value

    return check_output

  def run_sim( s ):
    s.dut.set_metadata( VerilogTranslationImportPass.enable, True )
    s.dut.set_metadata( VerilogVerilatorImportPass.vl_thread_number, 1 )
    s.dut.apply( VerilogPlaceholderPass() )
    s.dut = VerilogTranslationImportPass()( s.dut )

    s.dut.apply( DefaultPassGroup(linetrace=True) )
    s.dut.sim_reset()
    s.ref.apply( DefaultPassGroup(linetrace=False) )
    s.ref.sim_reset()

    # Apply the input cycle by cycle.
    inport_names = list(s.input_vector_list_map.keys())
    try:
      for input_vector in zip(*list(s.input_vector_list_map.values())):
        input_vector_map = { name : input_vector[i] for i, name in enumerate(inport_names) }
        s.apply_input_func(s.dut, input_vector_map)
        s.apply_input_func(s.ref, input_vector_map)

        s.dut.sim_tick()
        s.ref.sim_tick()

        s.check_output_func(s.dut, s.ref)
    finally:
      s.dut.finalize()

class SpecTestHarnessSrcSink( SpecTestHarnessBase, Component ):
  pass
