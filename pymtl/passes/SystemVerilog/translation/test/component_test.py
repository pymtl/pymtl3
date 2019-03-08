#=========================================================================
# component_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL models with multiple upblks and possible
# sub-components.
# 
# Author : Shunning Jiang

import pytest

from pymtl                      import *
from pclib.rtl                  import Adder, Subtractor
from pymtl.passes.SystemVerilog import TranslationPass
from pymtl.passes.utility       import expected_failure
from pymtl.passes.rast.errors   import PyMTLSyntaxError, PyMTLTypeError

def test_wrapped_noconnect_adder():
  class Adder_wrap_noc( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.adder = Adder( Bits32 )

      @s.update
      def up_in():
        s.adder.in0 = s.in_
        s.adder.in1 = s.in_

      @s.update
      def up_out():
        s.out = s.adder.out

  m = Adder_wrap_noc()
  m.elaborate()
  TranslationPass()( m )

def test_wrapped_noconnect_wire_adder():
  class Adder_wrap_wire( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.wire = Wire( Bits32 )

      s.adder = Adder( Bits32 )

      @s.update
      def up_in():
        s.wire = s.in_

      @s.update
      def up_wire():
        s.adder.in0 = s.wire
        s.adder.in1 = s.wire

      @s.update
      def up_out():
        s.out = s.adder.out

  m = Adder_wrap_wire()
  m.elaborate()
  TranslationPass()( m )

def test_wrapped_noconnect_slice_adder():
  class Adder_wrap_noc_slice( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits31 )
      s.out  = OutVPort( Bits32 )

      s.adder = Adder( Bits32 )

      @s.update
      def up_in():
        s.adder.in0[0:31] = s.in_
        s.adder.in1[0:31] = s.in_

      @s.update
      def up_out():
        s.out = s.adder.out

  m = Adder_wrap_noc_slice()
  m.elaborate()
  TranslationPass()( m )

def test_wrapped_connect_adder():
  class Adder_wrap_con( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.adder = Adder( Bits32 )( in0 = s.in_, in1 = s.in_, out = s.out )

  m = Adder_wrap_con()
  m.elaborate()
  TranslationPass()( m )

def test_wrapped_connect_wire_adder():
  class Adder_wrap_con_wire( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.wire = Wire( Bits32 )

      s.adder = Adder( Bits32 )( in0 = s.in_, in1 = s.in_, out = s.wire )

      s.connect( s.wire, s.out )

  m = Adder_wrap_con_wire()
  m.elaborate()
  TranslationPass()( m )

def test_wrapped_connect_two_child_modules_wire():
  class Adder_wrap_child_wire( RTLComponent ):
    def construct( s ):
      s.in0  = InVPort( Bits32 )
      s.in1  = InVPort( Bits32 )
      s.in2  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.tmp_in0 = Wire( Bits32 )
      s.tmp_out = Wire( Bits32 )

      s.connect( s.tmp_in0, s.in0 )
      s.connect( s.tmp_out, s.out )

      s.add = Adder( Bits32 )( in0 = s.tmp_in0, in1 = s.in1 )
      s.sub = Subtractor( Bits32 )( in0 = s.add.out, in1 = s.in2, out = s.tmp_out )

  m = Adder_wrap_child_wire()
  m.elaborate()
  TranslationPass()( m )

def test_multiple_if():
  class Foo_mul_if( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits2 )

      @s.update
      def up_if():
        if   s.in_ == ~s.in_:         s.out = s.in_
        elif s.in_ == s.in_ & s.in_:  s.out = ~s.in_
        elif s.in_ == s.in_ | s.in_:
          s.out = s.in_
          s.out = s.in_
          s.out = s.in_
        else:                         s.out = s.in_ + s.in_

  m = Foo_mul_if()
  m.elaborate()
  TranslationPass()( m )

def test_multiple_if_two_level():
  class Foo( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits2 )

      @s.update
      def up_if():
        if   s.in_ == ~s.in_:         s.out = s.in_
        elif s.in_ == s.in_ & s.in_:  s.out = ~s.in_
        elif s.in_ == s.in_ | s.in_:
          s.out = s.in_
          s.out = s.in_
          s.out = s.in_
        else:                         s.out = s.in_ + s.in_

  class Bar_if_2( RTLComponent ):
    def construct( s ):
      s.x = Foo()
      s.y = Wire( Bits2 )
      s.z = Wire( Bits2 )

      @s.update
      def up_y():
        s.y = s.x.out

      @s.update
      def up_z():
        s.x.in_ = s.z

  m = Bar_if_2()
  m.elaborate()
  TranslationPass()( m )

def test_bits_type():

  class Foo_bits( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits4 )

      @s.update
      def up_if():
        if   s.in_ == Bits2( 0 ):
          s.out = Bits4( 1 ) | Bits4( 2 )
          s.out = Bits4( 8 )
        else:
          s.out = Bits1( 0 ) # is this an error!
          s.out = Bits4( 1 )

  with expected_failure( PyMTLTypeError ):
    m = Foo_bits()
    m.elaborate()
    TranslationPass()( m )

def test_bits_type_in_self():
  class Foo_bits_s( RTLComponent ):
    def construct( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = s.Tout( 1 ) | s.Tout( 1 )
          s.out = s.Tout( 8 )
        else:
          s.out = s.Tout( 0 )

  m = Foo_bits_s()
  m.elaborate()
  TranslationPass()( m )

def test_bits_closure():

  class Foo_bits_closure( RTLComponent ):
    def construct( s ):
      nbits = 2

      Tin   = mk_bits( nbits )
      s.in_ = InVPort( Tin )
      Tout  = mk_bits( 1<<nbits )
      s.out = OutVPort( Tout )

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = Tout( 1 ) | Tout( 1 )
          s.out = Tout( 8 )
        else:
          s.out = Tout( 0 )

  m = Foo_bits_closure()
  m.elaborate()
  TranslationPass()( m )

def test_bits_value_closure():
  class Foo_bits_value_closure( RTLComponent ):
    def construct( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      s.one = 1
      eight = 8

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = s.Tout( s.one ) | s.Tout( s.one )
          s.out = s.Tout( eight )
        else:
          s.out = s.Tout( 0 )

  m = Foo_bits_value_closure()
  m.elaborate()
  TranslationPass()( m )

@pytest.mark.xfail( reason = 'Needs unimplemented task support' )
def test_bits_val_and_call():
  class Foo_bits_val_call( RTLComponent ):
    def construct( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      @s.func
      def foo( x ):
        s.out = x

      @s.update
      def up_if():
        if   s.in_ == s.Tin( 0 ):
          s.out = s.Tout( 1 ) | s.Tout( 1 )

        elif s.in_ == s.Tin( 1 ):
          s.out = s.Tout( 2 ) & s.Tout( 2 )
          s.out = ~s.Tout( 2 )

        elif s.in_ == s.Tin( 2 ):
          s.out = s.Tout( 4 ) < s.Tout( 3 )
          s.out = s.Tout( 4 ) if s.in_ == s.Tin( 2 ) else s.Tout( 5 )

        elif s.in_ == s.Tin( 3 ):
          s.out = s.Tout( 8 )

        else:
          s.out = s.Tout( 0 )
          foo( s.Tout( 0 ) )

  m = Foo_bits_val_call()
  m.elaborate()
  TranslationPass()( m )
