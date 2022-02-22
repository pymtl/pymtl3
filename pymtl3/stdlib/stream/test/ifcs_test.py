'''
==========================================================================
ifcs_test.py
==========================================================================
Test cases for stream interface adapters.

Author : Yanghui Ou
  Date : Feb 21, 2022
'''

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import (
    TestSrcCL as SourceCL,
    TestSinkCL as SinkCL,
    run_sim,
)
from pymtl3.stdlib.stream.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.stream.SourceRTL import SourceRTL
from pymtl3.stdlib.stream.SinkRTL import SinkRTL

#-------------------------------------------------------------------------
# DepUnit
#-------------------------------------------------------------------------
# Force rdy depends on val.
# This is to test whether the adapter causes combinational loop.

class DepUnit( Component ):
  def construct( s, Type ):
    s.recv = RecvIfcRTL( Type )
    s.send = SendIfcRTL( Type )

    s.recv.rdy //= lambda: s.recv.val & s.send.rdy
    s.send.val //= s.recv.val
    s.send.msg //= s.recv.msg

  def line_trace( s ):
    return f'{s.recv}(){s.send}'

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class ThClRTL( Component ):
  def construct( s, Type, msgs, rdy_dep_val=False ):

    msgs   = [ Type(x) for x in msgs ]
    s.src  = SourceCL( Type, msgs )
    s.sink = SinkRTL ( Type, msgs )

    if rdy_dep_val:
      s.dep = DepUnit( Type )
      s.src.send //= s.dep.recv
      s.dep.send //= s.sink.recv
    else:
      s.src.send //=s.sink.recv

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f'{s.src.line_trace()}>()>{s.sink.line_trace()}'

#-------------------------------------------------------------------------
# test_cl_rtl
#-------------------------------------------------------------------------

@pytest.mark.parametrize( 'dep', [ False, True ] )
def test_cl_rtl_simple( dep, cmdline_opts ):
  msgs = [ 0xdeadbeef, 0x0000ffff, 0xffff0000 ]
  th   = ThClRTL( Bits32, msgs, dep )
  run_sim( th, cmdline_opts )

@pytest.mark.parametrize( 'dep', [ False, True ] )
def test_cl_rtl_src_delay( dep, cmdline_opts ):
  msgs = [ 0xdeadbeef, 0x0000ffff, 0xffff0000 ] * 7
  th   = ThClRTL( Bits32, msgs, dep )

  th.set_param( 'top.src.construct',  initial_delay=10, interval_delay=3 )
  run_sim( th, cmdline_opts )

@pytest.mark.parametrize( 'dep', [ False, True ] )
def test_cl_rtl_sink_delay( dep, cmdline_opts ):
  msgs = [ 0xdeadbeef, 0x0000ffff, 0xffff0000 ] * 7
  th   = ThClRTL( Bits32, msgs, dep )

  th.set_param( 'top.sink.construct', initial_delay=20, interval_delay=5 )
  run_sim( th, cmdline_opts )

@pytest.mark.parametrize( 'dep', [ False, True ] )
def test_cl_rtl_rand_delay( dep, cmdline_opts ):
  msgs = [ 0xdeadbeef, 0x0000ffff, 0xffff0000 ] * 7
  th   = ThClRTL( Bits32, msgs, dep )

  th.set_param( 'top.src.construct',  interval_delay=3 )
  th.set_param( 'top.sink.construct', interval_delay=5 )
  run_sim( th, cmdline_opts )
