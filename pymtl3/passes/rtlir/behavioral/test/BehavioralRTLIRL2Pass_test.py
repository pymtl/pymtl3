#=========================================================================
# BehavioralRTLIRL2Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 2 behavioral RTLIR passes.

The L2 generation, L2 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

import pytest

from pymtl3.datatypes import Bits1, Bits2, Bits4, Bits32, bitstruct
from pymtl3.dsl import Component, InPort, OutPort, Wire
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL2Pass import (
    BehavioralRTLIRGenL2Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL2Pass import (
    BehavioralRTLIRTypeCheckL2Pass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.elaborate()
  m.apply( BehavioralRTLIRGenL2Pass() )
  m.apply( BehavioralRTLIRTypeCheckL2Pass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L2_lambda_connect( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.out //= lambda: s.in_ + Bits32(42)
  a = A()
  a._rtlir_test_ref = { '_lambda__s_out' : CombUpblk( '_lambda__s_out', [
    Assign( Attribute( Base( a ), 'out' ),
            BinOp(Attribute(Base(a), 'in_'), Add(), SizeCast(32, Number(42))), True
        ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L2_add_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) + s
  with expected_failure( PyMTLTypeError, "rhs of binop should be signal/const" ):
    do_test( A() )

def test_L2_inv_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = ~s
  with expected_failure( PyMTLTypeError, "only applies to signals and consts" ):
    do_test( A() )

def test_L2_for_start_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        for i in range( s, 8, 1 ):
          s.out = ~Bits1( 1 )
  with expected_failure( PyMTLTypeError, "must be a constant expression" ):
    do_test( A() )

def test_L2_for_end_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        for i in range( 0, s, 1 ):
          s.out = ~Bits1( 1 )
  with expected_failure( PyMTLTypeError, "must be a constant expression" ):
    do_test( A() )

def test_L2_for_step_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        for i in range( 0, 8, s ):
          s.out = ~Bits1( 1 )
  with expected_failure( PyMTLTypeError, "must be a constant expression" ):
    do_test( A() )

def test_L2_if_cond_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        if s:
          s.out = Bits1( 1 )
        else:
          s.out = ~Bits1( 1 )
  with expected_failure( PyMTLTypeError, "condition of if must be a signal" ):
    do_test( A() )

def test_L2_ifexp_cond_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1(1) if s else ~Bits1(1)
  with expected_failure( PyMTLTypeError, "condition of if-exp must be a signal" ):
    do_test( A() )

def test_L2_ifexp_body_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s if 1 else ~Bits1(1)
  with expected_failure( PyMTLTypeError, "body of if-exp must be a signal" ):
    do_test( A() )

def test_L2_ifexp_orelse_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1(1) if 1 else s
  with expected_failure( PyMTLTypeError, "else branch of if-exp must be a signal" ):
    do_test( A() )

def test_L2_if_cond_bool( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        if s.in_:
          s.out = Bits1(1)
        else:
          s.out = ~Bits1(1)
  with expected_failure( PyMTLTypeError, "cannot be converted to bool" ):
    do_test( A() )

def test_L2_for_step_zero( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        for i in range( 0, 4, 0 ):
          s.out = Bits1( 1 )
  with expected_failure( PyMTLTypeError, "step of for-loop cannot be zero" ):
    do_test( A() )

def test_L2_for_step_variable( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits2 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        for i in range( 0, 4, s.in_ ):
          s.out = Bits1( 1 )
  with expected_failure( PyMTLTypeError, "step of a for-loop must be a constant" ):
    do_test( A() )

def test_L2_ifexp_cond_bool( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1(1) if s.in_ else ~Bits1(1)
  with expected_failure( PyMTLTypeError, "cannot be converted to bool" ):
    do_test( A() )

def test_L2_ifexp_body_else_diff_type( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1(1) if 1 else s.in_
  with expected_failure( PyMTLTypeError, "must have the same type" ):
    do_test( A() )

def test_L2_unary_not_cast_to_bool( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = not s.in_
  with expected_failure( PyMTLTypeError, "cannot be cast to bool" ):
    do_test( A() )

def test_L2_bool_cast_to_bool( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) and s.in_
  with expected_failure( PyMTLTypeError, "cannot be cast into bool" ):
    do_test( A() )

def test_L2_binop_non_vector( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) + s.in_
  with expected_failure( PyMTLTypeError, "should be of vector type" ):
    do_test( A() )

#-------------------------------------------------------------------------
# PyMTL syntax errors
#-------------------------------------------------------------------------

def test_L2_call_bool( do_test ):
  Bool = rdt.Bool
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = Bool( Bits1(1) )
  with expected_failure( PyMTLSyntaxError, "bool values cannot be instantiated explicitly" ):
    do_test( A() )

def test_L2_tmp_var_used_before_assignement( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = u + Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "tmpvar u used before assignment" ):
    do_test( A() )

def test_L2_for_else( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        for i in range(4):
          s.out = Bits4( 1 )
        else:
          s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "for loops cannot have 'else' branch" ):
    do_test( A() )

def test_L2_for_index_signal( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = Wire( Bits4 )
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        for s.in_ in range(4):
          s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "loop index must be a temporary variable" ):
    do_test( A() )

def test_L2_for_index_redefined( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        for i in range(4):
          for i in range(4):
            s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "Redefinition of loop index i" ):
    do_test( A() )

def test_L2_for_iter_name( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits2 )
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        for i in s.in_:
          s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "only use range() after 'in'" ):
    do_test( A() )

def test_L2_for_iter_call_non_range( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      def foo(): pass
      @s.update
      def upblk():
        for i in foo():
          s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "only use range() after 'in'" ):
    do_test( A() )

def test_L2_for_iter_range_arg_0( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        for i in range():
          s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "1~3 arguments should be given to range" ):
    do_test( A() )

def test_L2_for_iter_range_arg_4( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        for i in range( 0, 4, 1, 1 ):
          s.out = Bits4( 1 )
  with expected_failure( PyMTLSyntaxError, "1~3 arguments should be given to range" ):
    do_test( A() )

def test_L2_invalid_op_is( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) is Bits1( 1 )
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( A() )

def test_L2_invalid_op_is_not( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) is not Bits1( 1 )
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( A() )

def test_L2_invalid_op_in( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) in Bits1( 1 )
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( A() )

def test_L2_invalid_op_not_in( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) not in Bits1( 1 )
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( A() )

def test_L2_invalid_op_floor_div( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = Bits1( 1 ) // Bits1( 1 )
  with expected_failure( PyMTLSyntaxError, "not supported" ):
    do_test( A() )

def test_L2_compare_terms( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = Bits1( 0 ) <= Bits2( 1 ) <= Bits2( 2 )
  with expected_failure( PyMTLSyntaxError, "Comparison can only have 2 operands" ):
    do_test( A() )

#-------------------------------------------------------------------------
# PyMTL syntax errors for unsupported Python syntax
#-------------------------------------------------------------------------

def test_Break( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        for i in range(42): break
  with expected_failure( PyMTLSyntaxError, "invalid operation: break" ):
    do_test( A() )

def test_Continue( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        for i in range(42): continue
  with expected_failure( PyMTLSyntaxError, "invalid operation: continue" ):
    do_test( A() )
