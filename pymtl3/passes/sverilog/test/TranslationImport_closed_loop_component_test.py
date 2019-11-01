#=========================================================================
# TranslationImport_closed_loop_component_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component."""

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, reproduce_failure, settings

from pymtl3.datatypes import Bits1, Bits16, Bits32, bitstruct, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, Wire, connect
from pymtl3.passes.rtlir.util.test_utility import do_test

from ..util.test_utility import closed_loop_component_test

too_slow = [ HealthCheck.too_slow ]

def local_do_test( m ):
  closed_loop_component_test( m, m._data )

# Use @given(st.data()) to draw input vector inside the test function
#  - also note that data should the rightmost argument of the test function
# Set deadline to None to avoid checking how long each test spin is
# Set max_examples to limit the number of attempts after multiple successes
# Suppress `too_slow` healthcheck to avoid marking a long test as failed
@given(st.data())
@settings(deadline = None, max_examples = 5, suppress_health_check = too_slow)
@pytest.mark.parametrize("Type", [Bits16, Bits32])
def test_adder( do_test, Type, data ):
  class A( Component ):
    def construct( s, Type ):
      s.in_1 = InPort( Type )
      s.in_2 = InPort( Type )
      s.out = OutPort( Type )
      @s.update
      def add_upblk():
        s.out = s.in_1 + s.in_2
    def line_trace( s ): return "sum = " + str( s.out )
  a = A( Type )
  a._data = data
  do_test( a )

@given(st.data())
@settings(deadline = None, max_examples = 5, suppress_health_check = too_slow)
@pytest.mark.parametrize(
  "Type, n_ports", [ (Bits16, 2), (Bits16, 4), (Bits32, 2), (Bits32, 4) ]
)
def test_mux( do_test, Type, n_ports, data ):
  class A( Component ):
    def construct( s, Type, n_ports ):
      s.in_ = [ InPort( Type ) for _ in range(n_ports) ]
      s.sel = InPort( mk_bits( clog2(n_ports) ) )
      s.out = OutPort( Type )
      @s.update
      def add_upblk():
        s.out = s.in_[ s.sel ]
    def line_trace( s ): return "out = " + str( s.out )
  a = A( Type, n_ports )
  a._data = data
  do_test( a )

@given(st.data())
@settings(deadline = None, max_examples = 5, suppress_health_check = too_slow)
def test_struct( do_test, data ):
  @bitstruct
  class strc:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( strc )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
    def line_trace( s ): return "out = " + str( s.out )
  a = A()
  a._data = data
  do_test( a )

@given(st.data())
@settings(deadline = None, max_examples = 10, suppress_health_check = too_slow)
def test_nested_struct( do_test, data ):
  @bitstruct
  class inner_struct:
    bar: Bits32
  @bitstruct
  class strc:
    foo: Bits32
    inner: inner_struct
    packed_array: [ [ Bits16 ]*2 ] *3
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( strc )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      s.out_sum = OutPort( Bits16 )
      s.sum = [ Wire( Bits16 ) for _ in range(3) ]
      @s.update
      def upblk():
        for i in range(3):
          s.sum[i] = s.in_.packed_array[i][0] + s.in_.packed_array[i][1]
        s.out_sum = s.sum[0] + s.sum[1] + s.sum[2]
      connect( s.out_foo, s.in_.foo )
      connect( s.out_bar, s.in_.inner.bar )
    def line_trace( s ): return "out_sum = " + str( s.out_sum )
  a = A()
  a._data = data
  do_test( a )

@given(st.data())
@settings(deadline = None, max_examples = 10, suppress_health_check = too_slow)
def test_subcomp( do_test, data ):
  @bitstruct
  class inner_struct:
    bar: Bits32
  @bitstruct
  class strc:
    foo: Bits32
    inner: inner_struct
    packed_array: [ [ Bits16 ]*2 ] *3
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      connect( s.out, 0 )
  class A( Component ):
    def construct( s ):
      s.b = B()
      s.in_ = InPort( strc )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      s.out_sum = OutPort( Bits16 )
      s.sum = [ Wire( Bits16 ) for _ in range(3) ]
      @s.update
      def upblk():
        for i in range(3):
          s.sum[i] = s.in_.packed_array[i][0] + s.in_.packed_array[i][1]
        s.out_sum = s.sum[0] + s.sum[1] + s.sum[2]
      connect( s.out_foo, s.b.out )
      connect( s.out_bar, s.in_.inner.bar )
    def line_trace( s ): return "out_sum = " + str( s.out_sum )
  a = A()
  a._data = data
  do_test( a )

# Test contributed by Cheng Tan
@given( st.data() )
@settings( deadline = None, max_examples = 5 )
@pytest.mark.parametrize( "Type", [ Bits16, Bits32 ] )
def test_index_static( do_test, Type, data ):
  class A( Component ):
    def construct( s, Type ):
      s.in_ = [InPort ( Type ) for _ in range(2)]
      s.out = [OutPort( Type ) for _ in range(2)]
      @s.update
      def index_upblk():
        if s.in_[0] > s.in_[1]:
          s.out[0] = Type(1)
          s.out[1] = Type(0)
        else:
          s.out[0] = Type(0)
          s.out[1] = Type(1)

    def line_trace( s ): return "s.in0  = " + str( s.in_[0] ) +\
                                "s.in1  = " + str( s.in_[1] ) +\
                                "s.out0 = " + str( s.out[0] ) +\
                                "s.out1 = " + str( s.out[1] )
  a = A( Type )
  a._data = data
  do_test( a )
