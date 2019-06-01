"""
========================================================================
Placeholder_test.py
========================================================================

Author : Shunning Jiang
Date   : June 1, 2019
"""
from pymtl3.datatypes import *
from pymtl3.dsl import InPort, OutPort, Placeholder, Component, WR, U

def test_placeholder_no_upblk():

  class Wrong( Placeholder, Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      @s.update
      def up_x():
        s.out = s.in_ + 1
  a = Wrong()
  a.elaborate()

def test_placeholder_no_constraints():

  class Wrong( Placeholder, Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.add_constraints( U(s.out) < WR(s.out) ) # this is obvious wrong
      print (123)
  a = Wrong()
  a.elaborate()

class Foo( Placeholder, Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = OutPort( mk_bits(nbits) )

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

    s.inner = Foo( 32 )( in_ = s.in_, out = s.out )

  def line_trace( s ):
    return s.inner.line_trace()

def test_dumb_foo():

  foo = Foo( 32 )
  foo.elaborate()
  # should elaborate just fine ..

def test_foo_as_writer():
  foo = Foo( 32 )
  foo_wrap = Foo_wrap( 32 )

  foo_wrap.elaborate()

def test_foo_delete_then_add():
  foo = Foo( 32 )
  foo_wrap = Foo_wrap( 32 )

  foo_wrap.elaborate()
  connections = foo_wrap.delete_component( foo_wrap.foo )
  foo_wrap.add_component( foo_wrap, "inner" , Real(), reconnect=connections )

def test_foo_replaced_by_real():
  foo = Foo( 32 )
  foo_wrap = Foo_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_component( foo_wrap.inner, Real() )
