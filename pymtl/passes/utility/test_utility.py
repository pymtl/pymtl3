#=========================================================================
# test_utility.py
#=========================================================================
# This file provides some useful utility that might be needed by some
# test cases.
#
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest

from pymtl                   import *
from pymtl.passes.PassGroups import SimpleSim, SimpleSimDumpDAG
from pclib.rtl.TestSource    import TestBasicSource as TestSource
from pclib.rtl.TestSink      import TestBasicSink   as TestSink

from contextlib              import contextmanager

#-------------------------------------------------------------------------
# do_test
#-------------------------------------------------------------------------
# Makes sure the tests only call the local_do_test function in their
# modules. From PyMTL v2.

@pytest.fixture
def do_test( request ):
  return request.module.local_do_test

#-------------------------------------------------------------------------
# expected_failure
#-------------------------------------------------------------------------
# This decorator is used to mark a test case as expected to fail because
# throwing a specific exception is the correct behavior. 
# Not to be confused with pytest.xfail, which is commonly used to mark
# tests related to unimplemented functionality.

@contextmanager
def expected_failure( exception = Exception ):
  """Mark one test case as expected failure, which only passes the test
  when it throws an expected exception."""

  try:
    yield
  except exception:
    pass
  except:
    raise Exception( func.__name__ + ' test unexpectedly passed!' )

#-------------------------------------------------------------------------
# run_translation_test
#-------------------------------------------------------------------------

def run_translation_test( model, test_vec, TranslationPass, ImportPass ):

  #-----------------------------------------------------------------------
  # Parse the test vector header
  #-----------------------------------------------------------------------
  
  # We convert the readable test vector format into a dict-based
  # structure that will be used to drive the simulation.

  header = test_vec[0].split()
  types  = test_vec[1]
  test_vec = test_vec[2:]

  signal_pos = {}
  pos_signal = []

  inports, outports = [], []
  inport_types, outport_types = {}, {}

  for idx, (port_name, port_type) in enumerate( zip(header, types) ):
    if port_name.startswith( '*' ):
      outports.append( port_name[1:] )
      outport_types[ port_name[1:] ] = port_type
      signal_pos[ port_name[1:] ] = idx
    else:
      inports.append( port_name )
      inport_types[ port_name ] = port_type
      signal_pos[ port_name ] = idx
    pos_signal.append( port_name )

  input_val, output_val = {}, {}

  # Initialize the input/output value dict with empty lists

  for port_name in inports:  input_val[ port_name ]  = []
  for port_name in outports: output_val[ port_name ] = []

  for vec in test_vec:
    assert len( vec ) == ( len( inports ) + len( outports ) )
    for idx, value in enumerate( vec ):
      if pos_signal[ idx ].startswith( '*' ):
        output_val[ pos_signal[ idx ][1:] ].append( value )
      else:
        input_val[ pos_signal[ idx ] ].append( value )

  #-----------------------------------------------------------------------
  # Construct the test harness
  #-----------------------------------------------------------------------

  model.elaborate()
  model.apply( TranslationPass() )
  model.apply( ImportPass() )

  dut = model._pass_simple_import.imported_model

  class TestHarness( RTLComponent ):
    def construct( s, dut, inport_types, outport_types, input_val, output_val ):

      s.dut = dut
      s.inport_types = inport_types
      s.outport_types = outport_types
      s.input_val = input_val
      s.output_val = output_val

      # Setup test sources/sinks
      s.srcs = [ TestSource( inport_types[inport_name], input_val[inport_name] )\
        for inport_name in input_val.keys()
      ]
      s.sinks = [ TestSink( outport_types[outport_name], output_val[outport_name] )\
        for outport_name in output_val.keys()
      ]

      # Connect all srcs/sinks to ports of dut
      for idx, inport_name in enumerate(input_val.keys()):
        exec( 's.connect( s.srcs[idx].out, s.dut.{name} )'\
          .format( name = inport_name ) ) in globals(), locals()

      for idx, outport_name in enumerate(output_val.keys()):
        exec( 's.connect( s.sinks[idx].in_, s.dut.{name} )'\
          .format( name = outport_name ) ) in globals(), locals()

  test_harness = TestHarness( dut, inport_types, outport_types, input_val, output_val )

  #-----------------------------------------------------------------------
  # Run the simulation
  #-----------------------------------------------------------------------

  # test_harness.apply( SimpleSimDumpDAG )
  test_harness.apply( SimpleSim )

  for cycle in xrange( len( test_vec ) ):
    test_harness.tick()
