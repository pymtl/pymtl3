#=========================================================================
# test_utility.py
#=========================================================================
# This file provides some useful utility that might be needed by some
# test cases.
#
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest

from contextlib import contextmanager

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

def run_translation_test( model, test_vec ):
  from pymtl.passes.import_     import SimpleImportPass
  from pymtl.passes.translation import SystemVerilogTranslationPass
  from pymtl.passes.PassGroups  import SimpleSim

  #-----------------------------------------------------------------------
  # Parse the test vector header
  #-----------------------------------------------------------------------
  
  # We convert the readable test vector format into a dict-based
  # structure that will be used to drive the simulation.

  header = test_vec[0].split()
  test_vec = test_vec[1:]

  signal_pos = {}
  pos_signal = []

  inports, outports = [], []

  for idx, port in enumerate( header ):
    if port.startswith( '*' ):
      outports.append( port[1:] )
      signal_pos[ port[1:] ] = idx
    else:
      inports.append( port )
      signal_pos[ port ] = idx
    pos_signal.append( port )

  input_val, output_val = {}, {}

  # Initialize the input/output value dict with empty lists

  for port in inports:  input_val[ port ]  = []
  for port in outports: output_val[ port ] = []

  for vec in test_vec:
    assert len( vec ) == ( len( inports ) + len( outports ) )
    for idx, value in enumerate( vec ):
      if pos_signal[ idx ].startswith( '*' ):
        output_val[ pos_signal[ idx ][1:] ].append( value )
      else:
        input_val[ pos_signal[ idx ] ].append( value )

  #-----------------------------------------------------------------------
  # Run the simulation
  #-----------------------------------------------------------------------

  model.elaborate()
  model.apply( SystemVerilogTranslationPass() )
  model.apply( SimpleImportPass() )
  sim = model._pass_simple_import.imported_model
  sim.apply( SimpleSim )

  for cycle in xrange( len( test_vec ) ):

    # feed input values
    for inport in inports:
      sim.__dict__[inport] = input_val[inport][cycle]

    # tick the model
    sim.tick()

    # check output values
    for outport in outports:
      assert check_port( sim.__dict__[outport], output_val[outport][cycle] )

def check_port( obj, ref ):
  if isinstance( obj, list ):
    for _obj, _ref in zip( obj, ref ):
      if not check_port( _obj, _ref ):
        return False
  return True
