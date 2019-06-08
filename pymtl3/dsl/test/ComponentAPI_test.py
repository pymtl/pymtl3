"""
========================================================================
ComponentAPI_test.py
========================================================================

Author : Shunning Jiang
Date   : June 2, 2019
"""
from __future__ import absolute_import, division, print_function

import random
from collections import deque

from pymtl3.datatypes import *
from pymtl3.dsl import Component, InPort, OutPort, Placeholder, Wire, method_port, CallerPort, M, U
from pymtl3.dsl.errors import InvalidAPICallError

from .sim_utils import simple_sim_pass


def test_api_not_elaborated():

  class X( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      @s.update
      def up_x():
        s.out = s.in_ + 1

  class Y( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.x = X()( in_ = s.in_, out = s.out )

  a = Y()
  a.elaborate()
  try:
    a.x.get_all_update_blocks()
  except InvalidAPICallError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidAPICallError.")

# The following two tests cases test x.replace_component()

class Foo_shamt( Placeholder, Component ):
  def construct( s, shamt=1 ):
    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits32 )

    # Nothing here

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Real_shamt( Component ):
  def construct( s, shamt=1 ):
    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits32 )
    @s.update
    def up_real():
      s.out = s.in_ << shamt

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Real_shamt2( Component ):
  def construct( s, shamt=1 ):
    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits32 )
    @s.update
    def up_real():
      s.out = s.in_ + shamt

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Foo_shamt_list_wrap( Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = [ OutPort( mk_bits(nbits) ) for i in range(5) ]

    s.inner = [ Foo_shamt( i )( in_ = s.in_, out = s.out[i] ) for i in range(5) ]

  def line_trace( s ):
    return "|".join( [ x.line_trace() for x in s.inner ] )

def test_real_replaced_by_real2():

  class Real_wrap( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.w   = Wire( mk_bits(nbits) )
      s.connect( s.w, s.out )

      s.inner = Real_shamt( 5 )( in_ = s.in_, out = s.w )

    def line_trace( s ):
      return s.inner.line_trace()

  foo_wrap = Real_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_component( foo_wrap.inner, Real_shamt2, check=True )

  simple_sim_pass( foo_wrap )
  foo_wrap.sim_reset()

  foo_wrap.in_ = Bits32(100)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 105

  foo_wrap.in_ = Bits32(3)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 8

def test_replace_component_list_of_foo_by_real():

  foo_wrap = Foo_shamt_list_wrap( 32 )

  foo_wrap.elaborate()
  order = range(5)
  random.shuffle( order )
  for i in order:
    foo_wrap.replace_component( foo_wrap.inner[i], Real_shamt )

  simple_sim_pass( foo_wrap )

  print()
  foo_wrap.in_ = Bits32(16)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

  foo_wrap.in_ = Bits32(4)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

def test_replace_component_list_of_real_by_real2():

  foo_wrap = Foo_shamt_list_wrap( 32 )

  order = range(5)
  random.shuffle( order )

  foo_wrap.elaborate()

  for i in order:
    foo_wrap.replace_component( foo_wrap.inner[i], Real_shamt )

  random.shuffle( order )
  for i in order:
    foo_wrap.replace_component( foo_wrap.inner[i], Real_shamt2 )

  print(len(foo_wrap._dsl.connect_order))
  simple_sim_pass( foo_wrap )

  print()
  foo_wrap.in_ = Bits32(16)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

  foo_wrap.in_ = Bits32(4)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

def test_mix_cl_rtl_constraints():

  class Source( Component ):

    def construct( s, msgs ):
      s.msgs = deque( msgs )

      s.req     = CallerPort()
      s.req_rdy = CallerPort()

      s.v = 0
      @s.update
      def up_src():
        s.v = None
        if s.req_rdy() and s.msgs:
          s.v = s.msgs.popleft()
          s.req( s.v )

  class CL2RTL( Component ):

    def construct( s ):
      s.send_rdy = InPort( Bits1 )
      s.send_en  = OutPort( Bits1 )
      s.send_msg = OutPort( Bits32 )

      s.entry = None

      @s.update_on_edge
      def up_clear():
        if s.send_en: # update_on_edge reverse this
          s.entry = None

      @s.update
      def up_send_rtl():
        if s.entry is None:
          s.send_en  = Bits1( 0 )
          s.send_msg = Bits32( 0 )
        else:
          s.send_en  = s.send_rdy
          s.send_msg = s.entry

      s.add_constraints(
        U( up_clear )   < M(s.recv),
        U( up_clear )   < M(s.recv_rdy),

        M( s.recv_rdy ) > U( up_send_rtl ),
        M( s.recv )     > U( up_send_rtl ),
      )

    @method_port
    def recv( s, msg ):
      s.entry = msg

    @method_port
    def recv_rdy( s ):
      return s.entry is None

  class DUT( Component ):

    def construct( s ):
      s.recv_rdy = OutPort( Bits1 )
      s.recv_en  = InPort( Bits1 )
      s.recv_msg = InPort( Bits32 )

      s.peitian = Wire(Bits1)
      s.yanghui = Wire(Bits32)

      @s.update
      def up_dut():
        s.recv_rdy = Bits1(1)
        s.peitian = s.recv_en
        s.yanghui = s.recv_msg

  class Top( Component ):
    def construct( s ):
      s.src = Source([1,2,3,4])
      s.adp = CL2RTL()( recv = s.src.req, recv_rdy = s.src.req_rdy )
      s.dut = DUT()( recv_rdy = s.adp.send_rdy,
                     recv_en  = s.adp.send_en,
                     recv_msg = s.adp.send_msg,
                    )
  x = Top()
  x.elaborate()
  from pymtl3.passes import DynamicSim
  for y in DynamicSim:
    y(x)

  for y in x._sched.schedule:
    print(y)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
  x.tick()
  print(x.dut.recv_en, x.dut.recv_rdy, x.dut.recv_msg)
