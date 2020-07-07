#=========================================================================
# TranslationImport_closed_loop_component_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component."""
import pytest
from hypothesis import HealthCheck, given, reproduce_failure, settings
from hypothesis import strategies as st

from pymtl3.datatypes import Bits1, Bits16, Bits32, bitstruct, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, Wire, connect
from pymtl3.passes.testcases import (
    CaseGenericAdderComp,
    CaseGenericConditionalDriveComp,
    CaseGenericMuxComp,
    CaseNestedStructConnectWireComp,
    CaseNestedStructConnectWireSubComp,
    CaseStructConnectWireComp,
)

from ..util.test_utility import closed_loop_component_test

too_slow = [ HealthCheck.too_slow ]

def local_do_test( m, data ):
  closed_loop_component_test( m, data )

# Use @given(st.data()) to draw input vector inside the test function
#  - also note that data should the rightmost argument of the test function
# Set deadline to None to avoid checking how long each test spin is
# Set max_examples to limit the number of attempts after multiple successes
# Suppress `too_slow` healthcheck to avoid marking a long test as failed

@given(st.data())
@settings(deadline = None, max_examples = 5, suppress_health_check = too_slow)
@pytest.mark.parametrize("Type", [Bits16, Bits32])
def test_generic_adder( Type, data ):
  local_do_test( CaseGenericAdderComp.DUT(Type), data )

@given(st.data())
@settings(deadline = None, max_examples = 5, suppress_health_check = too_slow)
@pytest.mark.parametrize(
  "Type, n_ports", [ (Bits16, 2), (Bits16, 4), (Bits32, 2), (Bits32, 4) ]
)
def test_mux( Type, n_ports, data ):
  local_do_test( CaseGenericMuxComp.DUT(Type, n_ports), data )

@given(st.data())
@settings(deadline = None, max_examples = 5, suppress_health_check = too_slow)
def test_struct( data ):
  local_do_test( CaseStructConnectWireComp.DUT(), data )

@given(st.data())
@settings(deadline = None, max_examples = 10, suppress_health_check = too_slow)
def test_nested_struct( data ):
  local_do_test( CaseNestedStructConnectWireComp.DUT(), data )

@given(st.data())
@settings(deadline = None, max_examples = 10, suppress_health_check = too_slow)
def test_subcomp( data ):
  local_do_test( CaseNestedStructConnectWireSubComp.DUT(), data )

# Test contributed by Cheng Tan
@given( st.data() )
@settings( deadline = None, max_examples = 5 )
@pytest.mark.parametrize( "Type", [ Bits16, Bits32 ] )
def test_index_static( Type, data ):
  local_do_test( CaseGenericConditionalDriveComp.DUT(Type), data )
