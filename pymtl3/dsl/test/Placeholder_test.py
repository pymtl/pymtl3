"""
========================================================================
Placeholder_test.py
========================================================================

Author : Shunning Jiang
Date   : June 1, 2019
"""
from pymtl3.datatypes import *
from pymtl3.dsl import InPort, OutPort, Wire, Placeholder, Component, WR, U
from pymtl3.dsl.errors import InvalidPlaceholderError, LeftoverPlaceholderError
from sim_utils import simple_sim_pass

def test_placeholder_no_upblk():

  class Wrong( Placeholder, Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      @s.update
      def up_x():
        s.out = s.in_ + 1
  try:
    a = Wrong()
    a.elaborate()
  except InvalidPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidPlaceholderError.")

def test_placeholder_no_constraints():

  class Wrong( Placeholder, Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.add_constraints( U(s.out) < WR(s.out) ) # this is obvious wrong

  try:
    a = Wrong()
    a.elaborate()
  except InvalidPlaceholderError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidPlaceholderError.")

class Foo( Placeholder, Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = OutPort( mk_bits(nbits) )

    # Nothing here

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class SomeMsg( object ):
  def __init__( s, a=0, b=0 ):
    s.a = Bits16(a)
    s.b = Bits32(b)

class FooStruct( Placeholder, Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = OutPort( SomeMsg )

    # Nothing here

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Real( Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = OutPort( mk_bits(nbits) )
    @s.update
    def up_x2():
      s.out = s.in_ << 1

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Foo_wrap( Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = OutPort( mk_bits(nbits) )
    s.w   = Wire( mk_bits(nbits) )
    s.connect( s.w, s.out )

    s.inner = Foo( 32 )( in_ = s.in_, out = s.w )

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

      s.inner = FooStruct( 16 )( in_ = s.in_ )
      s.connect( s.inner.out.b, s.out )

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
  foo_wrap.replace_placeholder( foo_wrap.inner, Real, check=True )

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

def test_list_of_foo_replaced_by_different_real():

  class Foo( Placeholder, Component ):
    def construct( s, shamt=1 ):
      s.in_ = InPort ( Bits32 )
      s.out = OutPort( Bits32 )

      # Nothing here

    def line_trace( s ):
      return "{}>{}".format( s.in_, s.out )

  class Real( Component ):
    def construct( s, shamt=1 ):
      s.in_ = InPort ( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def up_x2():
        s.out = s.in_ << shamt

    def line_trace( s ):
      return "{}>{}".format( s.in_, s.out )

  class Foo_list_wrap( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = [ OutPort( mk_bits(nbits) ) for i in range(5) ]

      s.inner = [ Foo( i )( in_ = s.in_, out = s.out[i] ) for i in range(5) ]

    def line_trace( s ):
      return "|".join( [ x.line_trace() for x in s.inner ] )

  foo_wrap = Foo_list_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_placeholder( foo_wrap.inner[2], Real )
  foo_wrap.replace_placeholder( foo_wrap.inner[1], Real )
  foo_wrap.replace_placeholder( foo_wrap.inner[4], Real )
  foo_wrap.replace_placeholder( foo_wrap.inner[3], Real )
  foo_wrap.replace_placeholder( foo_wrap.inner[0], Real )

  simple_sim_pass( foo_wrap )

  print()
  foo_wrap.in_ = Bits32(16)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

  foo_wrap.in_ = Bits32(4)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
