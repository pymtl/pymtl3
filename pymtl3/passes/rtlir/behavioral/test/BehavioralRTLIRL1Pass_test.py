#=========================================================================
# BehavioralRTLIRL1Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 1 behavioral RTLIR passes.

The L1 generation, L1 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

import sys
from copy import copy, deepcopy

import pytest

from pymtl3.datatypes import (
    Bits1,
    Bits2,
    Bits4,
    Bits8,
    Bits16,
    Bits32,
    bitstruct,
    concat,
    sext,
    zext,
)
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL1Pass import (
    BehavioralRTLIRGenL1Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL1Pass import (
    BehavioralRTLIRTypeCheckL1Pass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure

# TODO: fix all tests with this mark, including in other files (grep!).
# (we use the mark instead of allowing failure more generally because this
#  prevents regressions in all the other tests that *pass* on Python 3)
# If a test passes despite the mark, just remove it from that test!
if sys.version_info[0] == 3:
  XFAIL_ON_PY3 = pytest.mark.xfail(strict=True)
else:
  XFAIL_ON_PY3 = lambda f: f


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.elaborate()
  m.apply( BehavioralRTLIRGenL1Pass() )
  m.apply( BehavioralRTLIRTypeCheckL1Pass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L1_assign_unagreeable( do_test ):
  @bitstruct
  class B:
    foobar: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = s.in_
  with expected_failure( PyMTLTypeError, "Unagreeable types" ):
    do_test( A() )

def test_L1_concat_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = concat( s, s.in_ )
  with expected_failure( PyMTLTypeError, "not a signal" ):
    do_test( A() )

def test_L1_zext_variable_nbits( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = zext( s.in_, s.in_ )
  with expected_failure( PyMTLTypeError, "not a constant number" ):
    do_test( A() )

def test_L1_zext_small_nbits( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = zext( s.in_, 4 )
  with expected_failure( PyMTLTypeError, "not greater" ):
    do_test( A() )

def test_L1_sext_variable_nbits( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = sext( s.in_, s.in_ )
  with expected_failure( PyMTLTypeError, "not a constant number" ):
    do_test( A() )

def test_L1_sext_small_nbits( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = sext( s.in_, 4 )
  with expected_failure( PyMTLTypeError, "not greater" ):
    do_test( A() )

def test_L1_wrong_attribute( do_test ):
  class A( Component ):
    def construct( s ):
      # s.in_ is not recognized by RTLIR and will be dropped
      s.in_ = 'string'
      s.out = OutPort( Bits16 )
      @s.update
      def upblk():
        s.out = s.in_
  with expected_failure( PyMTLTypeError, "does not have attribute in_" ):
    do_test( A() )

def test_L1_unsupported_attr( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = [ OutPort( Bits1 ) for _ in range(5) ]
      s.comp_array = [ B() for _ in range(5) ]
      @s.update
      def upblk():
        s.out = s.comp_array[ 0 ].out
  with expected_failure( PyMTLTypeError, "not supported at L1" ):
    do_test( A() )

def test_L1_array_index_out_of_range( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits1 ) for _ in range(4) ]
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[4]
  with expected_failure( PyMTLTypeError, "array index out of range" ):
    do_test( A() )

def test_L1_bit_sel_index_out_of_range( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[4]
  with expected_failure( PyMTLTypeError, "bit selection index out of range" ):
    do_test( A() )

def test_L1_index_on_struct( do_test ):
  @bitstruct
  class B:
    foo: [ Bits4 ] * 4
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[16]
  with expected_failure( PyMTLTypeError, "cannot perform index on Struct" ):
    do_test( A() )

def test_L1_slice_on_struct( do_test ):
  @bitstruct
  class B:
    foo: [ Bits4 ] * 4
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[0:16]
  with expected_failure( PyMTLTypeError, "cannot perform slicing on type Struct" ):
    do_test( A() )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_slice_l_ngt_r( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[4:0]
  with expected_failure( PyMTLTypeError, "must be larger than the lower bound" ):
    do_test( A() )

def test_L1_slice_variable_bound( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.slice_l = InPort( Bits2 )
      s.slice_r = InPort( Bits2 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[s.slice_l:s.slice_r]
  with expected_failure( PyMTLTypeError, "slice bounds must be constant" ):
    do_test( A() )

def test_L1_slice_out_of_range( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[0:5]
  with expected_failure( PyMTLTypeError, "slice out of width of signal" ):
    do_test( A() )

#-------------------------------------------------------------------------
# PyMTL type errors: unexpected types
#-------------------------------------------------------------------------

def test_L1_assign_lhs_const( do_test ):
  class A( Component ):
    def construct( s ):
      u, s.v = 42, 42
      @s.update
      def upblk():
        s.v = u
  with expected_failure( PyMTLTypeError, "must be a signal" ):
    do_test( A() )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_assign_lhs_component( do_test ):
  class B( Component ):
    def construct( s ):
      pass
  class A( Component ):
    def construct( s ):
      s.u = B()
      @s.update
      def upblk():
        s.u = 42
  with expected_failure( PyMTLTypeError, "must be a signal" ):
    do_test( A() )

def test_L1_assign_rhs_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s
  with expected_failure( PyMTLTypeError, "signal or const" ):
    do_test( A() )

def test_L1_zext_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = zext( s, 1 )
  with expected_failure( PyMTLTypeError, "only applies to signals" ):
    do_test( A() )

def test_L1_sext_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = sext( s, 1 )
  with expected_failure( PyMTLTypeError, "only applies to signals" ):
    do_test( A() )

def test_L1_size_cast_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = Bits32( s )
  with expected_failure( PyMTLTypeError, "size casting only applies to signals/consts" ):
    do_test( A() )

def test_L1_attr_signal( do_test ):
  @bitstruct
  class B:
    """Struct class used to trigger certain exception.

    Struct does not belong to level 1. It is just used for testing purposes.
    """
    foobar: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_.foobar
  with expected_failure( PyMTLTypeError, "base of an attribute must be a component" ):
    do_test( A() )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_index_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[ s ]
  with expected_failure( PyMTLTypeError, "signal or constant expression" ):
    do_test( A() )

def test_L1_index_base_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s[ 1 ]
  with expected_failure( PyMTLTypeError, "base of an index must be an array or signal" ):
    do_test( A() )

def test_L1_slice_lower_component( do_test ):
  class B( Component ):
    def construct( s ):
      pass
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.idx = B()
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = s.in_[ s.idx:4 ]
  with expected_failure( PyMTLTypeError, "constant expression" ):
    do_test( A() )

def test_L1_slice_upper_component( do_test ):
  class B( Component ):
    def construct( s ):
      pass
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.idx = B()
      s.out = OutPort( Bits4 )
      @s.update
      def upblk():
        s.out = s.in_[ 0:s.idx ]
  with expected_failure( PyMTLTypeError, "constant expression" ):
    do_test( A() )

def test_L1_slice_component( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s[ 0:4 ]
  with expected_failure( PyMTLTypeError, "base of a slice must be a signal" ):
    do_test( A() )

#-------------------------------------------------------------------------
# PyMTL syntax errors
#-------------------------------------------------------------------------

def test_L1_upblk_arg( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk( number ):
        u = number
  with expected_failure( PyMTLSyntaxError, "not have arguments" ):
    do_test( A() )

def test_L1_multi_assign( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        u = v = x = y
  with expected_failure( PyMTLSyntaxError, "multiple targets" ):
    do_test( A() )

def test_L1_copy_arg( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        u = copy(42, 10)
  with expected_failure( PyMTLSyntaxError, "takes exactly 1 argument" ):
    do_test( A() )

def test_L1_deepcopy_arg( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        u = deepcopy(42, 10)
  with expected_failure( PyMTLSyntaxError, "takes exactly 1 argument" ):
    do_test( A() )

def test_L1_slice_step( do_test ):
  class A( Component ):
    def construct( s ):
      v = 42
      @s.update
      def upblk():
        u = v[ 0:16:4 ]
  with expected_failure( PyMTLSyntaxError, "Slice with steps" ):
    do_test( A() )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_L1_illegal_subscript( do_test ):
  class A( Component ):
    def construct( s ):
      v = 42
      @s.update
      def upblk():
        u = v[ 0:8, 16:24 ]
  with expected_failure( PyMTLSyntaxError, "Illegal subscript" ):
    do_test( A() )

def test_L1_closure_freevar( do_test ):
  class B( Component ): pass
  class A( Component ):
    def construct( s ):
      v = B()
      @s.update
      def upblk():
        u = v
  with expected_failure( PyMTLSyntaxError, "not a sub-component" ):
    do_test( A() )

def test_L1_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        u = 42
  with expected_failure( PyMTLSyntaxError, "Temporary variable" ):
    do_test( A() )

#-------------------------------------------------------------------------
# Call-related syntax errors
#-------------------------------------------------------------------------

@XFAIL_ON_PY3
def test_L1_call_star_arg( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = x(*x)
  with expected_failure( PyMTLSyntaxError, "star argument" ):
    do_test( A() )

@XFAIL_ON_PY3
def test_L1_call_double_star_arg( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = x(**x)
  with expected_failure( PyMTLSyntaxError, "double-star argument" ):
    do_test( A() )

def test_L1_call_keyword_arg( do_test ):
  class A( Component ):
    def construct( s ):
      xx = 42
      @s.update
      def upblk():
        x = x(x=x)
  with expected_failure( PyMTLSyntaxError, "keyword argument" ):
    do_test( A() )

def test_L1_call_name( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = copy.copy( x )
  with expected_failure( PyMTLSyntaxError, "called but is not a name" ):
    do_test( A() )

def test_L1_call_not_found( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        t = undefined_func(u)
  with expected_failure( PyMTLSyntaxError, "function is not found" ):
    do_test( A() )

def test_L1_call_Bits_args( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = Bits32( 42, 42 )
  with expected_failure( PyMTLSyntaxError, "exactly one argument" ):
    do_test( A() )

def test_L1_call_concat_args( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = concat()
  with expected_failure( PyMTLSyntaxError, "at least one argument" ):
    do_test( A() )

def test_L1_call_zext_num_args( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = zext( s )
  with expected_failure( PyMTLSyntaxError, "exactly two arguments" ):
    do_test( A() )

def test_L1_call_sext_num_args( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        x = sext( s )
  with expected_failure( PyMTLSyntaxError, "exactly two arguments" ):
    do_test( A() )

def test_L1_call_unrecognized( do_test ):
  class A( Component ):
    def construct( s ):
      def foo(): pass
      @s.update
      def upblk():
        x = foo()
  with expected_failure( PyMTLSyntaxError, "Unrecognized method" ):
    do_test( A() )

def test_L1_call_global_unrecognized( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        t = do_test(u)
  with expected_failure( PyMTLSyntaxError, "Unrecognized method" ):
    do_test( A() )

#-------------------------------------------------------------------------
# PyMTL syntax errors for unsupported Python syntax
#-------------------------------------------------------------------------

def test_Expr( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        42
  with expected_failure( PyMTLSyntaxError, "Stand-alone expression" ):
    do_test( A() )

def test_Lambda( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = lambda: 42
  with expected_failure( PyMTLSyntaxError, "invalid operation: lambda function" ):
    do_test( A() )

def test_Dict( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = { 1:42 }
  with expected_failure( PyMTLSyntaxError, "invalid type: dict" ):
    do_test( A() )

def test_Set( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = { 42 }
  with expected_failure( PyMTLSyntaxError, "invalid type: set" ):
    do_test( A() )

def test_List( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = [ 42 ]
  with expected_failure( PyMTLSyntaxError, "invalid type: list" ):
    do_test( A() )

def test_Tuple( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = ( 42, )
  with expected_failure( PyMTLSyntaxError, "invalid type: tuple" ):
    do_test( A() )

def test_ListComp( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = [ 42 for _ in range(1) ]
  with expected_failure( PyMTLSyntaxError, "invalid operation: list comprehension" ):
    do_test( A() )

def test_SetComp( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = { 42 for _ in range(1) }
  with expected_failure( PyMTLSyntaxError, "invalid operation: set comprehension" ):
    do_test( A() )

def test_DictComp( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = { 1:42 for _ in range(1) }
  with expected_failure( PyMTLSyntaxError, "invalid operation: dict comprehension" ):
    do_test( A() )

def test_GeneratorExp( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = ( 42 for _ in range(1) )
  with expected_failure( PyMTLSyntaxError, "invalid operation: generator expression" ):
    do_test( A() )

def test_Yield( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = yield
  with expected_failure( PyMTLSyntaxError, "invalid operation: yield" ):
    do_test( A() )

@pytest.mark.xfail( reason = "Syntax not compatible with Python 3" )
def test_Repr( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        # Python 2 only: s.out = `42`
        s.out = repr(42)
  with expected_failure( PyMTLSyntaxError, "invalid operation: repr" ):
    do_test( A() )

def test_Str( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = '42'
  with expected_failure( PyMTLSyntaxError, "invalid operation: str" ):
    do_test( A() )

def test_Classdef( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        class c: pass
  with expected_failure( PyMTLSyntaxError, "invalid operation: classdef" ):
    do_test( A() )

def test_Delete( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        del u
  with expected_failure( PyMTLSyntaxError, "invalid operation: delete" ):
    do_test( A() )

def test_With( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        with u: 42
  with expected_failure( PyMTLSyntaxError, "invalid operation: with" ):
    do_test( A() )

def test_Raise( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        raise 42
  with expected_failure( PyMTLSyntaxError, "invalid operation: raise" ):
    do_test( A() )

@XFAIL_ON_PY3
def test_TryExcept( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        try: 42
        except: 42
  with expected_failure( PyMTLSyntaxError, "invalid operation: try-except" ):
    do_test( A() )

@XFAIL_ON_PY3
def test_TryFinally( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        try: 42
        finally: 42
  with expected_failure( PyMTLSyntaxError, "invalid operation: try-finally" ):
    do_test( A() )

def test_Import( do_test ):
  class A( Component ):
    def construct( s ):
      x = 42
      @s.update
      def upblk():
        import x
  with expected_failure( PyMTLSyntaxError, "invalid operation: import" ):
    do_test( A() )

def test_ImportFrom( do_test ):
  class A( Component ):
    def construct( s ):
      x = 42
      @s.update
      def upblk():
        from x import x
  with expected_failure( PyMTLSyntaxError, "invalid operation: import-from" ):
    do_test( A() )

@pytest.mark.xfail( reason = "Syntax not compatible with Python 3" )
def test_Exec( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        # Python 2 only: exec 42
        exec(42)
  with expected_failure( PyMTLSyntaxError, "invalid operation: exec" ):
    do_test( A() )

def test_Global( do_test ):
  class A( Component ):
    def construct( s ):
      u = 42
      @s.update
      def upblk():
        global u
  with expected_failure( PyMTLSyntaxError, "invalid operation: global" ):
    do_test( A() )

def test_Pass( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        pass
  with expected_failure( PyMTLSyntaxError, "invalid operation: pass" ):
    do_test( A() )

def test_While( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        while 42: 42
  with expected_failure( PyMTLSyntaxError, "invalid operation: while" ):
    do_test( A() )

@pytest.mark.xfail( reason = "PyMTL DSL AST parsing failed" )
def test_ExtSlice( do_test ):
  class A( Component ):
    def construct( s ):
      @s.update
      def upblk():
        42[ 1:2:3, 2:4:6 ]
  with expected_failure( PyMTLSyntaxError, "invalid operation: extslice" ):
    do_test( A() )
