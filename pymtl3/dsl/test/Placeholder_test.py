"""
========================================================================
Placeholder_test.py
========================================================================

Author : Shunning Jiang
Date   : June 1, 2019
"""
from collections import deque

from pymtl3.datatypes import *
from pymtl3.dsl import (
    WR,
    CalleeIfcCL,
    CalleePort,
    CallerPort,
    Component,
    InPort,
    M,
    OutPort,
    Placeholder,
    U,
    Wire,
    connect,
    method_port,
    non_blocking,
    update,
    update_once,
)
from pymtl3.dsl.errors import InvalidPlaceholderError, LeftoverPlaceholderError

from .sim_utils import simple_sim_pass


def test_placeholder_no_upblk():

  class Wrong( Placeholder, Component ):
    def construct( s, nbits=1 ):
      s.in_ = InPort ( nbits )
      s.out = OutPort( nbits )
      @update
      def up_x():
        s.out @= s.in_ + 1
  try:
    a = Wrong()
    a.elaborate()
  except InvalidPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidPlaceholderError.")

def test_placeholder_no_constraints():

  class Wrong( Placeholder, Component ):
    def construct( s, nbits=1 ):
      s.in_ = InPort ( nbits )
      s.out = OutPort( nbits )
      s.add_constraints( U(s.out) < WR(s.out) ) # this is obvious wrong

  try:
    a = Wrong()
    a.elaborate()
  except InvalidPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidPlaceholderError.")

class Foo( Placeholder, Component ):
  def construct( s, nbits=1 ):
    s.in_ = InPort ( nbits )
    s.out = OutPort( nbits )

    # Nothing here

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

@bitstruct
class SomeMsg:
  a: Bits16
  b: Bits32

class FooStruct( Placeholder, Component ):
  def construct( s, nbits=1 ):
    s.in_ = InPort ( nbits )
    s.out = OutPort( SomeMsg )

    # Nothing here

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Real( Component ):
  def construct( s, nbits=1 ):
    s.in_ = InPort ( nbits )
    s.out = OutPort( nbits )
    @update
    def up_x2():
      s.out @= s.in_ << 1

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Foo_wrap( Component ):
  def construct( s, nbits=1 ):
    s.in_ = InPort ( nbits )
    s.out = OutPort( nbits )
    s.w   = Wire( nbits )
    connect( s.w, s.out )

    s.inner = Foo( 32 )
    s.inner.in_ //= s.in_
    s.inner.out //= s.w

  def line_trace( s ):
    return s.inner.line_trace()

def test_dumb_foo():
  foo = Foo( 32 )
  foo.elaborate()
  # should elaborate just fine ..

def test_dumb_foo_cannot_simulate():
  foo = Foo( 32 )
  foo.elaborate()
  # should elaborate just fine ..
  try:
    simple_sim_pass( foo )
  except LeftoverPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown LeftoverPlaceholderError.")

def test_foo_as_writer():
  foo_wrap = Foo_wrap( 32 )

  foo_wrap.elaborate()
  try:
    simple_sim_pass( foo_wrap )
  except LeftoverPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown LeftoverPlaceholderError.")

def test_foo_field_as_writer():

  class FooStruct_wrap( Component ):
    def construct( s ):
      s.in_ = InPort ( Bits16 )
      s.out = OutPort( Bits32 )

      s.inner = FooStruct( 16 )
      s.inner.in_ //= s.in_
      connect( s.inner.out.b, s.out )

    def line_trace( s ):
      return s.inner.line_trace()

  foo_wrap = FooStruct_wrap()
  foo_wrap.elaborate()
  try:
    simple_sim_pass( foo_wrap )
  except LeftoverPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown LeftoverPlaceholderError.")

def test_foo_replaced_by_real():
  foo_wrap = Foo_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_component( foo_wrap.inner, Real, check=True )

  simple_sim_pass( foo_wrap )
  foo_wrap.sim_reset()

  foo_wrap.in_ = Bits32(100)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 200

  foo_wrap.in_ = Bits32(3)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 6


def test_cl_methodport_placeholder():

  class FooCL( Placeholder, Component ):
    def construct( s ):
      s.enq = CalleePort()
      s.deq = CalleePort()

  class FooCL_wrap( Component ):
    def construct( s ):
      s.enq = CalleePort()
      s.deq = CalleePort()
      s.foo = FooCL()
      s.foo.enq //= s.enq
      s.foo.deq //= s.deq

  class FooCL_top( Component ):
    def construct( s ):
      s.x = FooCL_wrap()

      s.counter = 0

      @update_once
      def up_enq():
        s.x.enq(s.counter + 1)
        s.counter += 1

      @update_once
      def up_recv():
        print(s.x.deq())

  class RealQueue( Component ):
    @method_port
    def enq( s, msg ):
      s.q.appendleft( msg )
    @method_port
    def deq( s ):
      return s.q.pop()

    def construct( s ):
      s.q = deque()
      s.add_constraints( M(s.enq) < M(s.deq) )

  a = FooCL_top()
  a.elaborate()

  a.replace_component( a.x.foo, RealQueue )

  simple_sim_pass( a )
  a.tick()
  a.tick()
  a.tick()

def test_cl_interface_placeholder():

  class FooCL( Placeholder, Component ):
    def construct( s, queue_type="none" ):
      s.enq = CalleeIfcCL()
      s.deq = CalleeIfcCL()

  class FooCL_wrap( Component ):
    def construct( s ):
      s.enq = CalleeIfcCL()
      s.deq = CalleeIfcCL()
      s.foo = FooCL()
      s.foo.enq //= s.enq
      s.foo.deq //= s.deq

  class FooCL_top( Component ):
    def construct( s ):
      s.x = FooCL_wrap()

      s.received = None
      s.counter = 0
      @update_once
      def up_enq():
        if s.x.enq.rdy():
          s.x.enq(s.counter + 1)
          s.counter += 1
        else:
          print("enq not rdy")

      @update_once
      def up_recv():
        if s.x.deq.rdy():
          s.received = s.x.deq()
          print(s.received)
        else:
          print("deq not rdy")

  class RealQueue( Component ):
    def construct( s, queue_type ):
      s.element = None

      if queue_type == "bypass":
        s.add_constraints( M( s.enq ) < M( s.deq ) )
      else:
        assert queue_type == "pipe"
        s.add_constraints( M( s.deq ) < M( s.enq ) )

    def empty( s ):
      return s.element is None

    @non_blocking( lambda s : s.empty() )
    def enq( s, ele ):
      s.element = ele

    @non_blocking( lambda s: not s.empty() )
    def deq( s ):
      ret = s.element
      s.element = None
      return ret

  a = FooCL_top()
  b = FooCL_top()

  a.set_param( "top.x.foo.construct", queue_type="pipe" )
  b.set_param( "top.x.foo.construct", queue_type="bypass" )

  a.elaborate()
  b.elaborate()

  a.replace_component( a.x.foo, RealQueue )
  b.replace_component( b.x.foo, RealQueue )

  simple_sim_pass( a )
  simple_sim_pass( b )

  a.tick()
  b.tick()
  assert a.received == None # pipe queue cannot receive the packet in the first cycle
  assert b.received == 1 # bypass queue receive the packet in the first cycle
  a.tick()
  b.tick()
  assert a.received == 1 # pipe queue cannot receive the packet in the first cycle
  assert b.received == 2 # bypass queue receive the packet in the first cycle

  a.tick()
  b.tick()
  assert a.received == 2 # pipe queue cannot receive the packet in the first cycle
  assert b.received == 3 # bypass queue receive the packet in the first cycle
