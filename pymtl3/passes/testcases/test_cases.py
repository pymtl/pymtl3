"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository.

Author : Peitian Pan
Date   : Dec 12, 2019
"""

from copy import copy, deepcopy

from pymtl3 import *
from pymtl3.passes.rtlir import RTLIRDataType as rdt

from .TestCase import AliasOf

#-------------------------------------------------------------------------
# Helper functions that create tv_in and tv_out
#-------------------------------------------------------------------------

# args: [attr, Bits, idx]
def _set( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_in_str = 'def tv_in( m, tv ):  \n'
  if len(args) == 0:
    _tv_in_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    if isinstance(Bits, str):
      _tv_in_str += f'  m.{attr} @= {Bits}( tv[{idx}] )\n'
    else:
      _tv_in_str += f'  m.{attr} @= {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_in_str, globals(), local_dict )
  return local_dict['tv_in']

# args: [attr, Bits, idx]
def _check( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_out_str = 'def tv_out( m, tv ):  \n'
  if len(args) == 0:
    _tv_out_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    if isinstance(Bits, str):
      _tv_out_str += f'  assert m.{attr} == {Bits}( tv[{idx}] )\n'
    else:
      _tv_out_str += f'  assert m.{attr} == {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_out_str, globals(), local_dict )
  return local_dict['tv_out']

#-------------------------------------------------------------------------
# Commonly used global variables
#-------------------------------------------------------------------------

STATE_IDLE = 0
STATE_WORK = 0
pymtl_Bits_global_freevar = Bits32( 42 )

#-------------------------------------------------------------------------
# Commonly used BitStructs
#-------------------------------------------------------------------------

@bitstruct
class Bits32Foo:
  foo: Bits32

@bitstruct
class Bits32Bar:
  bar: Bits32

@bitstruct
class Bits32x5Foo:
  foo: [ Bits32 ] * 5

@bitstruct
class NestedBits32Foo:
  foo: Bits32Foo

@bitstruct
class NestedStructPackedArray:
  foo: [ Bits32x5Foo ] * 5

@bitstruct
class NestedStructPackedPlusScalar:
  foo: Bits32
  bar: [Bits32]*2
  woo: Bits32Foo

@bitstruct
class ThisIsABitStructWithSuperLongName:
  foo: Bits32

@bitstruct
class MultiDimPackedArrayStruct:
  foo: Bits32
  inner: Bits32Bar
  packed_array: [ [ Bits16 ]*2 ] *3

@bitstruct
class StructTypeNameAsFieldName:
  StructTypeNameAsFieldName: Bits32

class StructUniqueA:
  @bitstruct
  class ST:
    a_foo: Bits16
    a_bar: Bits32

class StructUniqueB:
  @bitstruct
  class ST:
    b_foo: Bits16
    b_bar: Bits32

@bitstruct
class StructUnique:
  fst: StructUniqueA.ST
  snd: StructUniqueB.ST

#-------------------------------------------------------------------------
# Commonly used Interfaces
#-------------------------------------------------------------------------

class Bits32OutIfc( Interface ):
  def construct( s ):
    s.foo = OutPort( Bits32 )

class Bits32InIfc( Interface ):
  def construct( s ):
    s.foo = InPort( Bits32 )

class Bits32FooOutIfc( Interface ):
  def construct( s ):
    s.foo = OutPort( Bits32Foo )

class Bits32FooInIfc( Interface ):
  def construct( s ):
    s.foo = InPort( Bits32Foo )

class Bits32InValRdyIfc( Interface ):
  def construct( s ):
    s.msg = InPort( Bits32 )
    s.val = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )

class Bits32OutValRdyIfc( Interface ):
  def construct( s ):
    s.msg = OutPort( Bits32 )
    s.val = OutPort( Bits1 )
    s.rdy = InPort( Bits1 )

class Bits32MsgRdyIfc( Interface ):
  def construct( s ):
    s.msg = OutPort( Bits32 )
    s.rdy = InPort ( Bits1 )

class Bits32FooWireBarInIfc( Interface ):
  def construct( s ):
    s.foo = Wire( Bits32 )
    s.bar = InPort( Bits32 )

class Bits32ArrayStructInIfc( Interface ):
  def construct( s ):
    s.foo = [ InPort( Bits32Foo ) for _ in range(1) ]

# Nested interfaces

class ReqIfc( Interface ):
  def construct( s ):
    s.msg = InPort( Bits32 )
    s.val = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )

class MemReqIfc( Interface ):
  def construct( s ):
    s.memifc = ReqIfc()
    s.ctrl_foo = InPort( Bits1 )

class RespIfc( Interface ):
  def construct( s ):
    s.msg = OutPort( Bits32 )
    s.val = OutPort( Bits1 )
    s.rdy = InPort( Bits1 )

class MemRespIfc( Interface ):
  def construct( s ):
    s.memifc = RespIfc()
    s.ctrl_foo = OutPort( Bits1 )

#-------------------------------------------------------------------------
# Commonly used Components
#-------------------------------------------------------------------------

class Bits32InOutComp( Component ):
  def construct( s ):
    s.in_ = InPort( Bits32 )
    s.out = OutPort( Bits32 )

class Bits16InOutPassThroughComp( Component ):
  def construct( s ):
    s.in_ = InPort( Bits16 )
    s.out = OutPort( Bits16 )
    @update
    def pass_through():
      s.out @= s.in_

class Bits1OutComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits1 )

class Bits32OutComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits32 )

class Bits32OutDrivenComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits32 )
    connect( s.out, Bits32(42) )

class WrappedBits32OutComp( Component ):
  def construct( s ):
    s.comp = Bits32OutComp()

class Bits32OutTmpDrivenComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits32 )
    @update
    def upblk():
      u = Bits32(0)
      s.out @= u

class Bits32OutFreeVarDrivenComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits32 )
    @update
    def upblk():
      if 1:
        s.out @= STATE_IDLE
      else:
        s.out @= STATE_WORK

class Bits32OutDrivenSubComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits32 )
    s.ifc = Bits32OutValRdyIfc()
    connect( s.out, Bits32(42) )
    connect( s.ifc.msg, Bits32(42) )
    connect( s.ifc.val, Bits1(1) )

class Bits32ArrayStructIfcComp( Component ):
  def construct( s ):
    s.out = OutPort( Bits32 )
    s.ifc = [ Bits32ArrayStructInIfc() for _ in range(1) ]
    connect( s.out, s.ifc[0].foo[0].foo )

class Bits32DummyFooComp( Component ):
  def construct( s ):
    s.in_ = InPort( Bits32 )
    s.out = OutPort( Bits32 )
    connect( s.out, s.in_ )

class Bits32DummyBarComp( Component ):
  def construct( s ):
    s.in_ = InPort( Bits32 )
    s.out = OutPort( Bits32 )
    @update
    def upblk():
      s.out @= s.in_ + Bits32(42)

class TestCompExplicitModuleName( Component ):
  def construct( s ):
    s.in_ = InPort( 32 )
    from pymtl3.passes.backends.verilog import VerilogTranslationPass
    s.set_metadata( VerilogTranslationPass.explicit_module_name, "NewChildDUTName" )

#-------------------------------------------------------------------------
# Test Components
#-------------------------------------------------------------------------

class CaseBits32PortOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )

class CaseStructPortOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )

class CaseNestedStructPortOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( NestedBits32Foo )

class CasePackedArrayStructPortOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )

class CaseBits32x5PortOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]

class CaseBits32x5WireOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Wire( Bits32 ) for _ in range(5) ]

class CaseStructx5PortOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32Foo ) for _ in range(5) ]

class CaseBits32x5ConstOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32(42) for _ in range(5) ]

class CaseBits32MsgRdyIfcOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32MsgRdyIfc() for _ in range(5) ]

class CaseBits32InOutx5CompOnly:
  class DUT( Component ):
    def construct( s ):
      s.b = [ Bits32InOutComp() for _ in range(5) ]

class CaseBits32Outx3x2x1PortOnly:
  class DUT( Component ):
    def construct( s ):
      s.out = [[[OutPort(Bits32) for _ in range(1)] for _ in range(2)] for _ in range(3)]

class CaseBits32WireIfcOnly:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32FooWireBarInIfc()

class CaseBits32ClosureConstruct:
  class DUT( Component ):
    def construct( s ):
      foo = Bits32( 42 )
      s.fvar_ref = foo
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= foo

class CaseBits32ArrayClosureConstruct:
  class DUT( Component ):
    def construct( s ):
      foo = [ Bits32(42) for _ in range(5) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= foo[2]

class CaseBits32ClosureGlobal:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= pymtl_Bits_global_freevar

class CaseStructClosureGlobal:
  class DUT( Component ):
    def construct( s ):
      foo = InPort( Bits32Foo )
      s._foo = foo
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= foo.foo

class CaseStructUnique:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.ST_A_wire = Wire( StructUniqueA.ST )
      s.ST_B_wire = Wire( StructUniqueB.ST )
      @update
      def upblk():
        s.ST_A_wire @= StructUniqueA.ST(1, 2)
        s.ST_B_wire @= StructUniqueB.ST(3, 4)
        s.out @= s.ST_A_wire.a_bar + s.ST_B_wire.b_bar
  TV_IN = _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =\
  [
      [ 6 ],
      [ 6 ],
  ]

class CasePythonClassAttr:
  class DUT( Component ):
    def construct( s ):
      class Enum:
        int_attr = 42
        bit_attr = Bits32(1)
      s.out1 = OutPort( Bits32 )
      s.out2 = OutPort( Bits32 )
      @update
      def upblk():
        s.out1 @= Enum.int_attr
        s.out2 @= Enum.bit_attr
  TV_IN = _set()
  TV_OUT = \
  _check(
      'out1', Bits32, 0,
      'out2', Bits32, 1,
  )
  TV =\
  [
      [  42,   1,  ],
      [  42,   1,  ],
  ]

class CaseTypeBundle:
  class DUT( Component ):
    def construct( s ):
      class TypeBundle:
        BitsType = Bits32
        BitStructType = Bits32Foo
      s.out1 = OutPort( TypeBundle.BitsType )
      s.out2 = OutPort( TypeBundle.BitStructType )
      s.out3 = OutPort( TypeBundle.BitStructType )
      @update
      def upblk():
        s.out1 @= TypeBundle.BitsType(42)
        s.out2 @= TypeBundle.BitStructType(1)
        s.out3 @= 1
  TV_IN = _set()
  TV_OUT = \
  _check(
      'out1', Bits32, 0,
      'out2', Bits32Foo, 1,
      'out3', Bits32Foo, 2,
  )
  TV =\
  [
      [  42,   1,  1, ],
      [  42,   1,  1, ],
  ]

class CaseBoolTmpVarComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        matched = s.in_ == 0
        if matched:
          s.out @= 1
        else:
          s.out @= 0
  TV_IN = _set(
      'in_', Bits32, 0
  )
  TV_OUT = \
  _check(
      'out', Bits32, 1,
  )
  TV =\
  [
      [  0,   1,  ],
      [  1,   0,  ],
      [  1,   0,  ],
      [  0,   1,  ],
  ]

class CaseTmpVarInUpdateffComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update_ff
      def upblk():
        if ~s.reset:
          val_next = Bits32(42)
          s.out <<= val_next
  TV_IN = _set()
  TV_OUT = \
  _check(
      'out', Bits32, 0,
  )
  TV =\
  [
      [   0, ],
      [  42, ],
      [  42, ],
  ]

class CaseBits32FooToBits32Comp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_
  TV_IN = _set(
      'in_', Bits32Foo, 0
  )
  TV_OUT = \
  _check(
      'out', Bits32, 1,
  )
  TV =\
  [
      [    0,    0,  ],
      [   -1,   -1,  ],
      [   42,   42,  ],
      [  -42,  -42,  ],
  ]

class CaseBits32ToBits32FooComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32Foo )
      @update
      def upblk():
        s.out @= s.in_
  TV_IN = _set(
      'in_', Bits32, 0
  )
  TV_OUT = \
  _check(
      'out', Bits32Foo, 1,
  )
  TV =\
  [
      [    0,    0,  ],
      [   -1,   -1,  ],
      [   42,   42,  ],
      [  -42,  -42,  ],
  ]

class CaseIntToBits32FooComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32Foo )
      @update
      def upblk():
        s.out @= 42
  TV_IN = _set()
  TV_OUT = \
  _check(
      'out', Bits32Foo, 0,
  )
  TV =\
  [
      [ 42 ],
      [ 42 ],
      [ 42 ],
  ]

class CaseReducesInx3OutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @update
      def v_reduce():
        s.out @= reduce_and( s.in_1 ) & reduce_or( s.in_2 ) | reduce_xor( s.in_3 )
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
      'in_3', Bits32, 2,
  )
  TV_OUT = \
  _check( 'out', Bits1, 3 )
  TV =\
  [
      [  0,   1,    2,  1   ],
      [ -1,   1,   -1,  1   ],
      [  9,   8,    7,  1   ],
      [  9,   8,    0,  0   ],
  ]

class CaseBits16IndexBasicComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits16 ) for _ in range( 4 ) ]
      s.out = [ OutPort( Bits16 ) for _ in range( 2 ) ]
      @update
      def index_basic():
        s.out[ 0 ] @= s.in_[ 0 ] + s.in_[ 1 ]
        s.out[ 1 ] @= s.in_[ 2 ] + s.in_[ 3 ]

class CaseBits8Bits16MismatchAssignComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      @update
      def mismatch_width_assign():
        s.out @= s.in_

class CaseBits32Bits64SlicingBasicComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @update
      def slicing_basic():
        s.out[ 0:16 ] @= s.in_[ 16:32 ]
        s.out[ 16:32 ] @= s.in_[ 0:16 ]

class CaseBits16ConstAddComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits16 )
      @update
      def bits_basic():
        s.out @= s.in_ + Bits16( 10 )

class CaseSlicingOverIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits16 ) for _ in range( 10 ) ]
      s.out = [ OutPort( Bits16 ) for _ in range( 5 ) ]
      @update
      def index_bits_slicing():
        s.out[0][0:8] @= s.in_[1][8:16] + s.in_[2][0:8] + 10
        s.out[1] @= s.in_[3][0:16] + s.in_[4] + 1

class CaseSubCompAddComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits16 )
      s.b = Bits16InOutPassThroughComp()
      # There should be a way to check module connections?
      connect( s.in_, s.b.in_ )
      @update
      def multi_components_A():
        s.out @= s.in_ + s.b.out

class CaseIfBasicComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      @update
      def if_basic():
        if s.in_[ 0:8 ] == 255:
          s.out @= s.in_[ 8:16 ]
        else:
          s.out @= 0
  TV_IN = \
  _set( 'in_', Bits16, 0 )
  TV_OUT = \
  _check( 'out', Bits8, 1 )
  TV =\
  [
      [ 255,   0, ],
      [  -1, 255, ],
      [ 511,   1, ],
      [ 254,   0, ],
      [  42,   0, ],
      [   0,   0, ],
  ]

class CaseIfDanglingElseInnerComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          if 0:
            s.out @= s.in_1
          else:
            s.out @= s.in_2
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
  )
  TV_OUT = \
  _check( 'out', Bits32, 2 )
  TV =\
  [
      [    0,    -1,  -1 ],
      [   42,     0,   0 ],
      [   24,    42,  42 ],
      [   -2,    24,  24 ],
      [   -1,    -2,  -2 ],
  ]

class CaseIfDanglingElseOutterComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          if 0:
            s.out @= s.in_1
        else:
          s.out @= s.in_2
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
  )
  TV_OUT = \
  _check( 'out', Bits32, 2 )
  TV =\
  [
      [    0,    -1,   0 ],
      [   42,     0,   0 ],
      [   24,    42,   0 ],
      [   -2,    24,   0 ],
      [   -1,    -2,   0 ],
  ]

class CaseElifBranchComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          s.out @= s.in_1
        elif 0:
          s.out @= s.in_2
        else:
          s.out @= s.in_3
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
      'in_3', Bits32, 2,
  )
  TV_OUT = \
  _check( 'out', Bits32, 3 )
  TV =\
  [
      [    0,    -1,   0,  0 ],
      [   42,     0,  42, 42 ],
      [   24,    42,  24, 24 ],
      [   -2,    24,  -2, -2 ],
      [   -1,    -2,  -1, -1 ],
  ]

class CaseNestedIfComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          if 0:
            s.out @= s.in_1
          else:
            s.out @= s.in_2
        elif 0:
          if 1:
            s.out @= s.in_2
          else:
            s.out @= s.in_3
        else:
          if 1:
            s.out @= s.in_3
          else:
            s.out @= s.in_1
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
      'in_3', Bits32, 2,
  )
  TV_OUT = \
  _check( 'out', Bits32, 3 )
  TV =\
  [
      [    0,    -1,   0,  -1 ],
      [   42,     0,  42,   0 ],
      [   24,    42,  24,  42 ],
      [   -2,    24,  -2,  24 ],
      [   -1,    -2,  -1,  -2 ],
  ]

class CaseForBasicComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      @update
      def for_basic():
        for i in range( 8 ):
          s.out[ 2*i:2*i+1 ] @= s.in_[ 2*i:2*i+1 ] + s.in_[ 2*i+1:(2*i+1)+1 ]

class CaseForFreeVarStepComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      freevar = 1
      @update
      def upblk():
        for i in range( 0, 2, freevar ):
          s.out @= s.in_[0:8]

class CaseTypeNameAsFieldNameComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( StructTypeNameAsFieldName )
      s.out = OutPort( StructTypeNameAsFieldName )
      s.in_ //= s.out

class CaseForRangeLowerUpperStepPassThroughComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(0, 5, 2):
          s.out[i] @= s.in_[i]
        for i in range(1, 5, 2):
          s.out[i] @= s.in_[i]
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
      'in_[2]', Bits32, 2,
      'in_[3]', Bits32, 3,
      'in_[4]', Bits32, 4,
  )
  TV_OUT = \
  _check(
      'out[0]', Bits32, 5,
      'out[1]', Bits32, 6,
      'out[2]', Bits32, 7,
      'out[3]', Bits32, 8,
      'out[4]', Bits32, 9,
  )
  TV =\
  [
      [    0,    -1,   0,  -1,   0,    0,    -1,   0,  -1,   0, ],
      [   42,     0,  42,   0,  42,   42,     0,  42,   0,  42, ],
      [   24,    42,  24,  42,  24,   24,    42,  24,  42,  24, ],
      [   -2,    24,  -2,  24,  -2,   -2,    24,  -2,  24,  -2, ],
      [   -1,    -2,  -1,  -2,  -1,   -1,    -2,  -1,  -2,  -1, ],
  ]

class CaseForLoopEmptySequenceComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits4( 0b1111 )
        for i in range(0, 0):
          s.out[i] @= Bits1( 0 )
  TV_IN = _set()
  TV_OUT = _check( 'out', Bits4, 0 )
  TV =\
  [
      [0xF],
      [0xF],
  ]

class CaseIfExpBothImplicitComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= 1 if s.in_ else 0
  TV_IN = _set( 'in_', Bits32, 0 )
  TV_OUT = _check( 'out', Bits32, 1 )
  TV =\
  [
      [    0,    0, ],
      [    1,    1, ],
      [    1,    1, ],
      [    0,    0, ],
  ]

class CaseIfExpInForStmtComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(5):
          s.out[i] @= s.in_[i] if i == 1 else s.in_[0]
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
      'in_[2]', Bits32, 2,
      'in_[3]', Bits32, 3,
      'in_[4]', Bits32, 4,
  )
  TV_OUT = \
  _check(
      'out[0]', Bits32, 5,
      'out[1]', Bits32, 6,
      'out[2]', Bits32, 7,
      'out[3]', Bits32, 8,
      'out[4]', Bits32, 9,
  )
  TV =\
  [
      [    0,    -1,   0,  -1,   0,    0,    -1,   0,   0,   0, ],
      [   42,     0,  42,   0,  42,   42,     0,  42,  42,  42, ],
      [   24,    42,  24,  42,  24,   24,    42,  24,  24,  24, ],
      [   -2,    24,  -2,  24,  -2,   -2,    24,  -2,  -2,  -2, ],
      [   -1,    -2,  -1,  -2,  -1,   -1,    -2,  -1,  -1,  -1, ],
  ]

class CaseIfExpUnaryOpInForStmtComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(5):
          s.out[i] @= (~s.in_[i]) if i == 1 else s.in_[0]
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
      'in_[2]', Bits32, 2,
      'in_[3]', Bits32, 3,
      'in_[4]', Bits32, 4,
  )
  TV_OUT = \
  _check(
      'out[0]', Bits32, 5,
      'out[1]', Bits32, 6,
      'out[2]', Bits32, 7,
      'out[3]', Bits32, 8,
      'out[4]', Bits32, 9,
  )
  TV =\
  [
      [    0,    -1,   0,  -1,   0,    0,    ~-1,   0,   0,   0, ],
      [   42,     0,  42,   0,  42,   42,     ~0,  42,  42,  42, ],
      [   24,    42,  24,  42,  24,   24,    ~42,  24,  24,  24, ],
      [   -2,    24,  -2,  24,  -2,   -2,    ~24,  -2,  -2,  -2, ],
      [   -1,    -2,  -1,  -2,  -1,   -1,    ~-2,  -1,  -1,  -1, ],
  ]

class CaseIfBoolOpInForStmtComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(5):
          if ( s.in_[i] != 0 ) & ( ( s.in_[i+1] != 0 ) if i<4 else ( s.in_[4] != 0 )):
            s.out[i] @= s.in_[i]
          else:
            s.out[i] @= 0
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
      'in_[2]', Bits32, 2,
      'in_[3]', Bits32, 3,
      'in_[4]', Bits32, 4,
  )
  TV_OUT = \
  _check(
      'out[0]', Bits32, 5,
      'out[1]', Bits32, 6,
      'out[2]', Bits32, 7,
      'out[3]', Bits32, 8,
      'out[4]', Bits32, 9,
  )
  TV =\
  [
      [    0,    -1,   0,  -1,   0,     0,     0,    0,    0,    0, ],
      [   42,     0,  42,   0,  42,     0,     0,    0,    0,   42, ],
      [   24,    42,  24,  42,  24,    24,    42,   24,   42,   24, ],
      [   -2,    24,  -2,  24,  -2,    -2,    24,   -2,   24,   -2, ],
      [   -1,    -2,  -1,  -2,  -1,    -1,    -2,   -1,   -2,   -1, ],
  ]

class CaseIfTmpVarInForStmtComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(5):
          if ( s.in_[i]  != 0 ) & ( ( s.in_[i+1] != 0 ) if i<4 else ( s.in_[4] != 0 ) ):
            tmpvar = s.in_[i]
          else:
            tmpvar = b32(0)
          s.out[i] @= tmpvar
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
      'in_[2]', Bits32, 2,
      'in_[3]', Bits32, 3,
      'in_[4]', Bits32, 4,
  )
  TV_OUT = \
  _check(
      'out[0]', Bits32, 5,
      'out[1]', Bits32, 6,
      'out[2]', Bits32, 7,
      'out[3]', Bits32, 8,
      'out[4]', Bits32, 9,
  )
  TV =\
  [
    [    0,    -1,   0,  -1,   0,     0,     0,    0,    0,    0, ],
    [   42,     0,  42,   0,  42,     0,     0,    0,    0,   42, ],
    [   24,    42,  24,  42,  24,    24,    42,   24,   42,   24, ],
    [   -2,    24,  -2,  24,  -2,    -2,    24,   -2,   24,   -2, ],
    [   -1,    -2,  -1,  -2,  -1,    -1,    -2,   -1,   -2,   -1, ],
  ]

class CaseFixedSizeSliceComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = [ OutPort( Bits8 ) for _ in range(2) ]
      @update
      def upblk():
        for i in range(2):
          s.out[i] @= s.in_[i*8 : i*8 + 8]
  TV_IN = \
  _set( 'in_', Bits16, 0 )
  TV_OUT = \
  _check(
      'out[0]', Bits8, 1,
      'out[1]', Bits8, 2,
  )
  TV =\
  [
      [     -1, 0xff, 0xff ],
      [      1, 0x01, 0x00 ],
      [      7, 0x07, 0x00 ],
      [ 0xff00, 0x00, 0xff ],
      [ 0x3412, 0x12, 0x34 ],
      [ 0x9876, 0x76, 0x98 ],
  ]

class CaseTwoUpblksSliceComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits8 )
      @update
      def multi_upblks_1():
        s.out[ 0:4 ] @= s.in_
      @update
      def multi_upblks_2():
        s.out[ 4:8 ] @= s.in_

class CaseTwoUpblksFreevarsComp:
  class DUT( Component ):
    def construct( s ):
      STATE_IDLE = Bits2(0)
      STATE_WORK = Bits2(1)
      s.out = [ OutPort( Bits2 ) for _ in range(2) ]
      @update
      def multi_upblks_1():
        s.out[0] @= STATE_IDLE
      @update
      def multi_upblks_2():
        s.out[1] @= STATE_WORK

class CaseTwoUpblksStructTmpWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_foo = InPort( Bits32Foo )
      s.in_bar = InPort( Bits32Bar )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      @update
      def multi_upblks_1():
        u = s.in_foo
        s.out_foo @= u.foo
      @update
      def multi_upblks_2():
        u = s.in_bar
        s.out_bar @= u.bar

class CaseFlipFlopAdder:
  class DUT( Component ):
    def construct( s ):
      s.in0 = InPort( Bits32 )
      s.in1 = InPort( Bits32 )
      s.out0 = OutPort( Bits32 )
      @update_ff
      def update_ff_upblk():
        s.out0 <<= s.in0 + s.in1

class CaseConstSizeSlicingComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = [ OutPort( Bits8 ) for _ in range(2) ]
      @update
      def upblk():
        for i in range(2):
          s.out[i] @= s.in_[i*8 : i*8 + 8]

class CaseBits32TmpWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_ + 42
        s.out @= u

class CaseBits32MultiTmpWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_ + 42
        v = s.in_ + 40
        s.out @= u
        s.out @= v

class CaseBits32FreeVarToTmpVarComp:
  class DUT( Component ):
    def construct( s ):
      # STATE_IDLE = Bits32(0)
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = STATE_IDLE
        s.out @= u

class CaseBits32ConstBitsToTmpVarComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = Bits32(0)
        s.out @= u

class CaseBits32ConstIntToTmpVarComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = 1
        s.out @= u

class CaseBits32TmpWireAliasComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @update
      def multi_upblks_1():
        u = s.in_ + 42
        s.out[0] @= u
      @update
      def multi_upblks_2():
        u = s.in_ + 42
        s.out[1] @= u

class CaseStructTmpWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_
        s.out @= u.foo

class CaseTmpWireOverwriteConflictComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits16 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_1 + 42
        u = s.in_2 + 1
        s.out @= u

class CaseScopeTmpWireOverwriteConflictComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits16 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          u = s.in_1 + 42
          s.out @= u
        else:
          u = s.in_2 + 1
          s.out @= u

class CaseHeteroCompArrayComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out_1 = OutPort( Bits32 )
      s.out_2 = OutPort( Bits32 )
      comp_types = [ Bits32DummyFooComp, Bits32DummyBarComp ]
      s.comps = [ comp_types[i]() for i in range(2) ]
      s.comps[0].in_ //= s.in_1
      s.comps[1].in_ //= s.in_2
      s.comps[0].out //= s.out_1
      s.comps[1].out //= s.out_2
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
  )
  TV_OUT = \
  _check(
      'out_1', Bits32, 2,
      'out_2', Bits32, 3,
  )
  TV =\
  [
      [    0,     -1,     0,    41],
      [   42,      0,    42,    42],
      [   -1,     42,    -1,    84],
  ]

class CaseChildExplicitModuleName:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( 32 )
      s.child = TestCompExplicitModuleName()
      s.child.in_ //= s.in_
  TV_IN  = _set( 'in_', Bits32, 0 )
  TV_OUT = _check()
  TV =\
  [
      [ 0 ],
  ]

#-------------------------------------------------------------------------
# Test cases without errors
#-------------------------------------------------------------------------

class CaseSizeCastPaddingStructPort:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= Bits64( s.in_ )
  TV_IN = \
  _set(
      'in_', Bits32Foo, 0,
  )
  TV_OUT = \
  _check( 'out', Bits64, 1 )
  TV =\
  [
      [    0,     concat(   Bits32(0),     Bits32(0)  ) ],
      [   42,     concat(   Bits32(0),     Bits32(42) ) ],
      [   -1,     concat(   Bits32(0),     Bits32(-1) ) ],
  ]

class CaseBits32x2ConcatComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= concat( s.in_1, s.in_2 )
  TV_IN = \
  _set(
      'in_1', Bits32, 0,
      'in_2', Bits32, 1,
  )
  TV_OUT = \
  _check( 'out', Bits64, 2 )
  TV =\
  [
      [    0,    0,     concat(    Bits32(0),     Bits32(0) ) ],
      [   42,    0,     concat(   Bits32(42),     Bits32(0) ) ],
      [   42,   42,     concat(   Bits32(42),    Bits32(42) ) ],
      [   -1,   42,     concat(   Bits32(-1),    Bits32(42) ) ],
  ]

class CaseBits32x2ConcatConstComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= concat( Bits32(42), Bits32(0) )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits64, 0 )
  TV =\
  [
      [    concat(    Bits32(42),    Bits32(0) ) ],
  ]

class CaseBits32x2ConcatMixedComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= concat( s.in_, Bits32(0) )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits64, 1 )
  TV =\
  [
      [  42,  concat(    Bits32(42),    Bits32(0) ) ],
      [  -1,  concat(    Bits32(-1),    Bits32(0) ) ],
      [  -2,  concat(    Bits32(-2),    Bits32(0) ) ],
      [   2,  concat(     Bits32(2),    Bits32(0) ) ],
  ]

class CaseBits32x2ConcatFreeVarComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits33 )
      @update
      def upblk():
        s.out @= concat( s.in_, STATE_IDLE )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits33, 1 )
  TV =\
  [
      [  42,  concat(    Bits32(42),    Bits1(0) ) ],
      [  -1,  concat(    Bits32(-1),    Bits1(0) ) ],
      [  -2,  concat(    Bits32(-2),    Bits1(0) ) ],
      [   2,  concat(     Bits32(2),    Bits1(0) ) ],
  ]

class CaseBits32x2ConcatUnpackedSignalComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= concat( s.in_[0], s.in_[1] )
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
  )
  TV_OUT = \
  _check( 'out', Bits64, 2 )
  TV =\
  [
      [  42,   2,  concat(    Bits32(42),     Bits32(2) ) ],
      [  -1,  42,  concat(    Bits32(-1),    Bits32(42) ) ],
      [  -2,  -1,  concat(    Bits32(-2),    Bits32(-1) ) ],
      [   2,  -2,  concat(     Bits32(2),    Bits32(-2) ) ],
  ]

class CaseBits64SextInComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= sext( s.in_, 64 )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits64, 1 )
  TV =\
  [
      [  42,   sext(    Bits32(42),    64 ) ],
      [  -2,   sext(    Bits32(-2),    64 ) ],
      [  -1,   sext(    Bits32(-1),    64 ) ],
      [   2,   sext(     Bits32(2),    64 ) ],
  ]

class CaseBits64ZextInComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @update
      def upblk():
        s.out @= zext( s.in_, 64 )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits64, 1 )
  TV =\
  [
      [  42,   zext(    Bits32(42),    64 ) ],
      [  -2,   zext(    Bits32(-2),    64 ) ],
      [  -1,   zext(    Bits32(-1),    64 ) ],
      [   2,   zext(     Bits32(2),    64 ) ],
  ]

class CaseBits64TruncInComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits8 )
      @update
      def upblk():
        s.out @= trunc( s.in_, 8 )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits8, 1 )
  TV =\
  [
      [  42,   trunc(    Bits32(42),    8 ) ],
      [  -2,   trunc(    Bits32(-2),    8 ) ],
      [  -1,   trunc(    Bits32(-1),    8 ) ],
      [   2,   trunc(     Bits32(2),    8 ) ],
  ]

class CaseBits32BitSelUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[1]
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits1, 1 )
  TV =\
  [
      [   0,   0 ],
      [  -1,   1 ],
      [  -2,   1 ],
      [   2,   1 ],
  ]

class CaseBits64PartSelUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits64 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[4:36]
  TV_IN = \
  _set( 'in_', Bits64, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [   -1,   -1 ],
      [   -2,   -1 ],
      [   -4,   -1 ],
      [   -8,   -1 ],
      [  -16,   -1 ],
      [  -32,   -2 ],
      [  -64,   -4 ],
  ]

class CasePassThroughComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [    0,    0 ],
      [   42,   42 ],
      [   24,   24 ],
      [   -2,   -2 ],
      [   -1,   -1 ],
  ]

class CaseSequentialPassThroughComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update_ff
      def upblk():
        s.out <<= s.in_
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [    0,     0 ],
      [   42,     0 ],
      [   24,    42 ],
      [   -2,    24 ],
      [   -1,    -2 ],
  ]

class CaseConnectPassThroughLongNameComp:
  class DUT( Component ):
    def construct( s, T1, T2, T3, T4, T5, T6, T7 ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_ )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [    0,    0 ],
      [   42,   42 ],
      [   24,   24 ],
      [   -2,   -2 ],
      [   -1,   -1 ],
  ]

class CaseLambdaConnectComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.out //= lambda: s.in_ + 42
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [    0,   42 ],
      [   -1,   41 ],
      [    2,   44 ],
      [    1,   43 ],
      [   42,   84 ],
      [  -42,    0 ],
      [  -41,    1 ],
  ]

class CaseLambdaConnectWithListComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = [ OutPort( Bits32 ) for _ in range(2) ]
      s.out[1] //= lambda: s.in_ + 42

  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out[1]', Bits32, 1 )
  TV =\
  [
      [    0,   42 ],
      [   -1,   41 ],
      [    2,   44 ],
      [    1,   43 ],
      [   42,   84 ],
      [  -42,    0 ],
      [  -41,    1 ],
  ]

class CaseBits32FooInBits32OutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.foo
  TV_IN = \
  _set( 'in_', Bits32Foo, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [    0,   0 ],
      [   -1,  -1 ],
      [   42,  42 ],
      [   -2,  -2 ],
      [   10,  10 ],
      [  256, 256 ],
  ]

class CaseBits32FooKwargComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= Bits32Foo( foo = 42 )

class CaseBits32FooInstantiationComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32Foo )
      @update
      def upblk():
        s.out @= Bits32Foo( 42 )

class CaseConstStructInstComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32Foo()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.foo
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =\
  [
      [ 0 ],
  ]

class CaseStructPackedArrayUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
      s.out = OutPort( Bits96 )
      @update
      def upblk():
        s.out @= concat( s.in_.foo[0], s.in_.foo[1], s.in_.foo[2] )
  TV_IN = \
  _set( 'in_', Bits32x5Foo, 0 )
  TV_OUT = \
  _check( 'out', Bits96, 1 )
  TV =\
  [
      [  [ b32(0), b32(0), b32(0), b32(0),b32(0) ], concat( b32(0),   b32(0),   b32(0)  ) ],
      [  [ b32(-1),b32(-1),b32(-1),b32(0),b32(0) ], concat( b32(-1),  b32(-1),  b32(-1) ) ],
      [  [ b32(42),b32(42),b32(-1),b32(0),b32(0) ], concat( b32(42),  b32(42),  b32(-1) ) ],
      [  [ b32(42),b32(42),b32(42),b32(0),b32(0) ], concat( b32(42),  b32(42),  b32(42) ) ],
      [  [ b32(-1),b32(-1),b32(42),b32(0),b32(0) ], concat( b32(-1),  b32(-1),  b32(42) ) ],
  ]

class CaseConnectLiteralStructComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( NestedStructPackedPlusScalar )
      connect( s.out, NestedStructPackedPlusScalar( 42, [ b32(1), b32(2) ], Bits32Foo(3) ) )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', "(lambda x: x)", 0 )
  TV =\
  [
      [   NestedStructPackedPlusScalar(42, [ Bits32(1) , Bits32(2)  ], Bits32Foo(3) ) ],
  ]

class CaseNestedStructPackedArrayUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( NestedStructPackedPlusScalar )
      s.out = OutPort( Bits96 )
      @update
      def upblk():
        s.out @= concat( s.in_.bar[0], s.in_.woo.foo, s.in_.foo )
  TV_IN = \
  _set( 'in_', '(lambda x: x)', 0 )
  TV_OUT = \
  _check( 'out', Bits96, 1 )
  TV =\
  [
      [   NestedStructPackedPlusScalar(0, [ Bits32(0) , Bits32(0)  ], Bits32Foo(5) ), concat(   Bits32(0), Bits32(5),   Bits32(0) ) ],
      [  NestedStructPackedPlusScalar(-1, [ Bits32(-1), Bits32(-2) ], Bits32Foo(6) ), concat(  Bits32(-1), Bits32(6),  Bits32(-1) ) ],
      [  NestedStructPackedPlusScalar(-1, [ Bits32(42), Bits32(43) ], Bits32Foo(7) ), concat(  Bits32(42), Bits32(7),  Bits32(-1) ) ],
      [  NestedStructPackedPlusScalar(42, [ Bits32(42), Bits32(43) ], Bits32Foo(8) ), concat(  Bits32(42), Bits32(8),  Bits32(42) ) ],
      [  NestedStructPackedPlusScalar(42, [ Bits32(-1), Bits32(-2) ], Bits32Foo(9) ), concat(  Bits32(-1), Bits32(9),  Bits32(42) ) ],
  ]

class CaseConnectNestedStructPackedArrayComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( NestedStructPackedPlusScalar )
      s.out = OutPort( Bits96 )
      connect( s.out[0:32], s.in_.foo )
      connect( s.out[32:64], s.in_.woo.foo )
      connect( s.out[64:96], s.in_.bar[0] )
  TV_IN = \
  _set( 'in_', '(lambda x: x)', 0 )
  TV_OUT = \
  _check( 'out', Bits96, 1 )
  TV =\
  [
      [   NestedStructPackedPlusScalar(0, [ Bits32(0) , Bits32(0)  ], Bits32Foo(5) ), concat(   Bits32(0), Bits32(5),   Bits32(0) ) ],
      [  NestedStructPackedPlusScalar(-1, [ Bits32(-1), Bits32(-2) ], Bits32Foo(6) ), concat(  Bits32(-1), Bits32(6),  Bits32(-1) ) ],
      [  NestedStructPackedPlusScalar(-1, [ Bits32(42), Bits32(43) ], Bits32Foo(7) ), concat(  Bits32(42), Bits32(7),  Bits32(-1) ) ],
      [  NestedStructPackedPlusScalar(42, [ Bits32(42), Bits32(43) ], Bits32Foo(8) ), concat(  Bits32(42), Bits32(8),  Bits32(42) ) ],
      [  NestedStructPackedPlusScalar(42, [ Bits32(-1), Bits32(-2) ], Bits32Foo(9) ), concat(  Bits32(-1), Bits32(9),  Bits32(42) ) ],
  ]

class CaseInterfaceAttributeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32OutIfc()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.foo

class CaseArrayInterfacesComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32OutIfc() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[2].foo

class CaseBits32SubCompPassThroughComp:
  class DUT( Component ):
    def construct( s ):
      s.comp = Bits32OutComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.comp.out

class CaseArrayBits32SubCompPassThroughComp:
  class DUT( Component ):
    def construct( s ):
      s.comp = [ Bits32OutComp() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.comp[2].out

class CaseSubCompTmpDrivenComp:
  class DUT( Component ):
    def construct( s ):
      s.subcomp = Bits32OutTmpDrivenComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.subcomp.out
        s.out @= u

class CaseSubCompFreeVarDrivenComp:
  class DUT( Component ):
    def construct( s ):
      s.subcomp = Bits32OutFreeVarDrivenComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          s.out @= s.subcomp.out
        else:
          s.out @= STATE_IDLE

class CaseConstBits32AttrComp:
  class DUT( Component ):
    def construct( s ):
      s.const = [ Bits32(42) for _ in range(5) ]

class CaseInx2Outx2ConnectComp:
  class DUT( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out1 = OutPort( Bits32 )
      s.out2 = OutPort( Bits32 )
      connect( s.in_1, s.out1 )
      connect( s.in_2, s.out2 )

class CaseConnectPortIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = OutPort( Bits32 )
      connect( s.in_[2], s.out )

class CaseConnectInToWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.wire_ = [ Wire( Bits32 ) for _ in range(5) ]
      s.out = OutPort( Bits32 )
      connect( s.wire_[2], s.out )
      for i in range(5):
        connect( s.wire_[i], s.in_[i] )
  TV_IN = \
  _set(
      'in_[0]', Bits32, 0,
      'in_[1]', Bits32, 1,
      'in_[2]', Bits32, 2,
      'in_[3]', Bits32, 3,
      'in_[4]', Bits32, 4,
  )
  TV_OUT = \
  _check( 'out', Bits32, 5 )
  TV =\
  [
      [ 0,   0,    0,  0,  0,   0 ],
      [ 0,   0,   42,  0,  0,  42 ],
      [ 0,   0,   24,  0,  0,  24 ],
      [ 0,   0,   -2,  0,  0,  -2 ],
      [ 0,   0,   -1,  0,  0,  -1 ],
  ]

class CaseWiresDrivenComp:
  class DUT( Component ):
    def construct( s ):
      s.foo = Wire( Bits32 )
      s.bar = Wire( Bits4 )
      @update
      def upblk():
        s.foo @= 42
        s.bar @= 0

class CaseBits32Wirex5DrivenComp:
  class DUT( Component ):
    def construct( s ):
      s.foo = [ Wire( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(5):
          s.foo[i] @= 0

class CaseStructWireDrivenComp:
  class DUT( Component ):
    def construct( s ):
      s.foo = Wire( Bits32Foo )
      @update
      def upblk():
        s.foo.foo @= 42

class CaseStructConstComp:
  class DUT( Component ):
    def construct( s ):
      s.struct_const = Bits32Foo()

class CaseNestedPackedArrayStructComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( NestedStructPackedArray )
      s.out = OutPort( Bits32x5Foo )
      connect( s.in_.foo[1], s.out )

class CaseConnectConstToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.const_ = [ 42 for _ in range(5) ]
      s.out = OutPort( Bits32 )
      connect( s.const_[2], s.out )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =\
  [
      [ 42 ],
  ]

class CaseConnectBitSelToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.in_[0], s.out )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits1, 1 )
  TV =\
  [
      [    0,   0, ],
      [    1,   1, ],
      [    2,   0, ],
      [    3,   1, ],
      [   -1,   1, ],
      [   -2,   0, ],
  ]

class CaseConnectSliceToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits4 )
      connect( s.in_[4:8], s.out )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits4, 1 )
  TV =\
  [
      [    0,   0, ],
      [    1,   0, ],
      [    2,   0, ],
      [    3,   0, ],
      [   -1,  -1, ],
      [   -2,  -1, ],
  ]

class CaseConnectBitsConstToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      connect( s.out, Bits32(0) )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =\
  [
      [ 0 ],
  ]

class CaseConnectStructAttrToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )

class CaseConnectArrayStructAttrToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo[1] )
  TV_IN = \
  _set( 'in_', Bits32x5Foo, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [  [ b32(0), b32(0), b32(0), b32(0),b32(0) ], 0,  ],
      [  [ b32(-1),b32(-1),b32(-1),b32(0),b32(0) ], -1, ],
      [  [ b32(42),b32(42),b32(-1),b32(0),b32(0) ], 42, ],
      [  [ b32(42),b32(42),b32(42),b32(0),b32(0) ], 42, ],
      [  [ b32(-1),b32(-1),b32(42),b32(0),b32(0) ], -1, ],
  ]

class CaseConnectConstStructAttrToOutComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32Foo( 42 )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =[ [ 42 ] ]

class CaseBits32IfcInComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32InIfc()
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )

class CaseArrayBits32IfcInComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32InIfc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      connect( s.in_[1].foo, s.out )

class CaseBits32FooNoArgBehavioralComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32Foo )
      @update
      def upblk():
        s.out @= Bits32Foo()
  TV_IN = _set()
  TV_OUT = \
  _check( 'out', Bits32Foo, 0 )
  TV =\
  [
      [    0, ],
      [    0, ],
  ]

class CaseArrayBits32IfcInUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32InIfc() for _ in range(5) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[1].foo
  TV_IN = \
  _set(
      'in_[0].foo', Bits32, 0,
      'in_[1].foo', Bits32, 1,
  )
  TV_OUT = \
  _check( 'out', Bits32, 2 )
  TV =\
  [
      [    0,    0,      0 ],
      [    0,   42,     42 ],
      [   24,   42,     42 ],
      [   -2,   -1,     -1 ],
      [   -1,   -2,     -2 ],
  ]

class CaseConnectValRdyIfcComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32InValRdyIfc()
      s.out = Bits32OutValRdyIfc()
      # This will be automatically extended to connect all signals in
      # this interface!
      connect( s.out, s.in_ )
  TV_IN = \
  _set(
      'in_.val', Bits1, 0,
      'in_.msg', Bits32, 1,
      'out.rdy', Bits1, 2,
  )
  TV_OUT = \
  _check(
      'out.val', Bits1, 3,
      'out.msg', Bits32, 4,
      'in_.rdy', Bits1, 5,
  )
  TV =\
  [
      [    0,    42,   1,    0,    42,    1 ],
      [    1,    -1,   1,    1,    -1,    1 ],
      [    1,    -2,   0,    1,    -2,    0 ],
      [    0,     2,   0,    0,     2,    0 ],
      [    1,    24,   1,    1,    24,    1 ],
  ]

class CaseConnectValRdyIfcUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32InValRdyIfc()
      s.out = Bits32OutValRdyIfc()
      @update
      def upblk():
        s.out.val @= s.in_.val
        s.out.msg @= s.in_.msg
        s.in_.rdy @= s.out.rdy
  TV_IN = \
  _set(
      'in_.val', Bits1, 0,
      'in_.msg', Bits32, 1,
      'out.rdy', Bits1, 2,
  )
  TV_OUT = \
  _check(
      'out.val', Bits1, 3,
      'out.msg', Bits32, 4,
      'in_.rdy', Bits1, 5,
  )
  TV =\
  [
      [    0,    42,   1,    0,    42,    1 ],
      [    1,    -1,   1,    1,    -1,    1 ],
      [    1,    -2,   0,    1,    -2,    0 ],
      [    0,     2,   0,    0,     2,    0 ],
      [    1,    24,   1,    1,    24,    1 ],
  ]

class CaseConnectArrayBits32FooIfcComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32FooInIfc() for _ in range(2) ]
      s.out = [ Bits32FooOutIfc() for _ in range(2) ]
      for i in range(2):
        connect( s.out[i], s.in_[i] )
  TV_IN = \
  _set(
      'in_[0].foo.foo',   Bits32,  0,
      'in_[1].foo.foo',   Bits32,  1,
  )
  TV_OUT = \
  _check(
      'out[0].foo.foo',   Bits32,  2,
      'out[1].foo.foo',   Bits32,  3,
  )
  TV =\
  [
      [ 1,      0,    1,      0, ],
      [ 0,     42,    0,     42, ],
      [ 1,     42,    1,     42, ],
      [ 1,     -1,    1,     -1, ],
      [ 1,     -2,    1,     -2, ],
  ]

class CaseConnectArrayNestedIfcComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ MemReqIfc() for _ in range(2) ]
      s.out = [ MemRespIfc() for _ in range(2) ]
      for i in range(2):
        connect( s.out[i], s.in_[i] )
  TV_IN = \
  _set(
      'in_[0].ctrl_foo',   Bits1,  0,
      'in_[0].memifc.val', Bits1,  1,
      'in_[0].memifc.msg', Bits32, 2,
      'out[0].memifc.rdy', Bits1,  3,
      'in_[1].ctrl_foo',   Bits1,  4,
      'in_[1].memifc.val', Bits1,  5,
      'in_[1].memifc.msg', Bits32, 6,
      'out[1].memifc.rdy', Bits1,  7,
  )
  TV_OUT = \
  _check(
      'out[0].ctrl_foo',   Bits1,  8,
      'out[0].memifc.val', Bits1,  9,
      'out[0].memifc.msg', Bits32, 10,
      'in_[0].memifc.rdy', Bits1,  11,
      'out[1].ctrl_foo',   Bits1,  12,
      'out[1].memifc.val', Bits1,  13,
      'out[1].memifc.msg', Bits32, 14,
      'in_[1].memifc.rdy', Bits1,  15,
  )
  TV =\
  [
      [ 1,  1,      0,    0,    1,  1,      0,    0,  1,  1,      0,    0,    1,  1,      0,    0, ],
      [ 1,  0,     42,    1,    1,  0,     42,    1,  1,  0,     42,    1,    1,  0,     42,    1, ],
      [ 1,  1,     42,    0,    1,  1,     42,    0,  1,  1,     42,    0,    1,  1,     42,    0, ],
      [ 1,  1,     -1,    1,    1,  1,     -1,    1,  1,  1,     -1,    1,    1,  1,     -1,    1, ],
      [ 1,  1,     -2,    0,    1,  1,     -2,    0,  1,  1,     -2,    0,    1,  1,     -2,    0, ],
  ]

class CaseBits32IfcTmpVarOutComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.ifc = Bits32OutIfc()
      @update
      def upblk():
        u = s.ifc.foo
        s.out @= u

class CaseStructIfcTmpVarOutComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.ifc = Bits32FooInIfc()
      @update
      def upblk():
        u = s.ifc.foo
        s.out @= u.foo

class CaseBits32ConnectSubCompAttrComp:
  class DUT( Component ):
    def construct( s ):
      s.b = Bits32OutDrivenComp()
      s.out = OutPort( Bits32 )
      connect( s.out, s.b.out )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =[ [ 42 ] ]

class CaseBits32SubCompAttrUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.b = Bits32OutDrivenComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.b.out
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =\
  [
      [ 42 ],
  ]

class CaseConnectSubCompIfcHierarchyComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.ifc = Bits32OutValRdyIfc()
      s.subcomp = Bits32OutDrivenSubComp()
      connect( s.subcomp.out, s.out )
      connect( s.subcomp.ifc, s.ifc )
  TV_IN = \
  _set()
  TV_OUT = \
  _check(
      'out',     Bits32, 0,
      'ifc.msg', Bits32, 1,
      'ifc.val', Bits1,  2,
  )
  TV =[ [ 42, 42, 1 ] ]

class CaseConnectArraySubCompArrayStructIfcComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.b = [ Bits32ArrayStructIfcComp() for _ in range(1) ]
      connect( s.in_, s.b[0].ifc[0].foo[0].foo )
      connect( s.out, s.b[0].out )
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [ 42, 42 ],
      [  1,  1 ],
      [ -1, -1 ],
      [ -2, -2 ],
  ]

class CaseBehavioralArraySubCompArrayStructIfcComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.b = [ Bits32ArrayStructIfcComp() for _ in range(2) ]
      @update
      def upblk():
        for i in range(2):
          for j in range(1):
            s.b[i].ifc[j].foo[0].foo @= s.in_
        s.out @= s.b[1].out
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV =\
  [
      [ 42, 42 ],
      [  1,  1 ],
      [ -1, -1 ],
      [ -2, -2 ],
  ]

class CaseBits32ArrayConnectSubCompAttrComp:
  class DUT( Component ):
    def construct( s ):
      s.b = [ Bits32OutDrivenComp() for _ in range(5) ]
      s.out = OutPort( Bits32 )
      connect( s.out, s.b[1].out )
  TV_IN = \
  _set()
  TV_OUT = \
  _check(
      'out',     Bits32, 0,
  )
  TV =[ [ 42 ] ]

class CaseBits32ArraySubCompAttrUpblkComp:
  class DUT( Component ):
    def construct( s ):
      s.b = [ Bits32OutDrivenComp() for _ in range(5) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.b[1].out
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =\
  [
      [ 42 ],
  ]

class CaseComponentArgsComp:
  class DUT( Component ):
    def construct( s, foo, bar ):
      pass

class CaseComponentDefaultArgsComp:
  class DUT( Component ):
    def construct( s, foo, bar = Bits16(42) ):
      pass

class CaseMixedDefaultArgsComp:
  class DUT( Component ):
    def construct( s, foo, bar, woo = Bits32(0) ):
      pass

class CaseGenericAdderComp:
  class DUT( Component ):
    def construct( s, Type ):
      s.in_1 = InPort( Type )
      s.in_2 = InPort( Type )
      s.out = OutPort( Type )
      @update
      def add_upblk():
        s.out @= s.in_1 + s.in_2
    def line_trace( s ): return 'sum = ' + str(s.out)

class CaseGenericMuxComp:
  class DUT( Component ):
    def construct( s, Type, n_ports ):
      s.in_ = [ InPort( Type ) for _ in range(n_ports) ]
      s.sel = InPort( mk_bits( clog2(n_ports) ) )
      s.out = OutPort( Type )
      @update
      def add_upblk():
        s.out @= s.in_[ s.sel ]
    def line_trace( s ): return "out = " + str( s.out )

class CaseStructConnectWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
    def line_trace( s ): return "out = " + str( s.out )

class CaseNestedStructConnectWireComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( MultiDimPackedArrayStruct )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      s.out_sum = OutPort( Bits16 )
      s.sum = [ Wire( Bits16 ) for _ in range(3) ]
      @update
      def upblk():
        for i in range(3):
          s.sum[i] @= s.in_.packed_array[i][0] + s.in_.packed_array[i][1]
        s.out_sum @= s.sum[0] + s.sum[1] + s.sum[2]
      connect( s.out_foo, s.in_.foo )
      connect( s.out_bar, s.in_.inner.bar )
    def line_trace( s ): return "out_sum = " + str( s.out_sum )

class CaseNestedStructConnectWireSubComp:
  class DUT( Component ):
    def construct( s ):
      s.b = Bits32OutDrivenComp()
      s.in_ = InPort( MultiDimPackedArrayStruct )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      s.out_sum = OutPort( Bits16 )
      s.sum = [ Wire( Bits16 ) for _ in range(3) ]
      @update
      def upblk():
        for i in range(3):
          s.sum[i] @= s.in_.packed_array[i][0] + s.in_.packed_array[i][1]
        s.out_sum @= s.sum[0] + s.sum[1] + s.sum[2]
      connect( s.out_foo, s.b.out )
      connect( s.out_bar, s.in_.inner.bar )
    def line_trace( s ): return "out_sum = " + str( s.out_sum )

class CaseGenericConditionalDriveComp:
  class DUT( Component ):
    def construct( s, Type ):
      s.in_ = [InPort ( Type ) for _ in range(2)]
      s.out = [OutPort( Type ) for _ in range(2)]
      @update
      def index_upblk():
        if s.in_[0] > s.in_[1]:
          s.out[0] @= 1
          s.out[1] @= 0
        else:
          s.out[0] @= 0
          s.out[1] @= 1
    def line_trace( s ): return "s.in0  = " + str( s.in_[0] ) +\
                                "s.in1  = " + str( s.in_[1] ) +\
                                "s.out0 = " + str( s.out[0] ) +\
                                "s.out1 = " + str( s.out[1] )

class CaseBitSelOverBitSelComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[1][0] )
  TV_IN  = _set( 'in_', Bits32, 0 )
  TV_OUT = _check( 'out', Bits1, 1 )
  TV = \
  [
      [ 1, 0 ],
      [ 2, 1 ],
      [ 3, 1 ],
      [ 4, 0 ],
      [ 5, 0 ],
  ]

class CaseBitSelOverPartSelComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[0:4][0] )
  TV_IN  = _set( 'in_', Bits32, 0 )
  TV_OUT = _check( 'out', Bits1, 1 )
  TV = \
  [
      [ 1, 1 ],
      [ 2, 0 ],
      [ 3, 1 ],
      [ 4, 0 ],
      [ 5, 1 ],
  ]

class CasePartSelOverBitSelComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[1][0:1] )
  TV_IN  = _set( 'in_', Bits32, 0 )
  TV_OUT = _check( 'out', Bits1, 1 )
  TV = \
  [
      [ 1, 0 ],
      [ 2, 1 ],
      [ 3, 1 ],
      [ 4, 0 ],
      [ 5, 0 ],
  ]

class CasePartSelOverPartSelComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[0:4][0:1] )
  TV_IN  = _set( 'in_', Bits32, 0 )
  TV_OUT = _check( 'out', Bits1, 1 )
  TV = \
  [
      [ 1, 1 ],
      [ 2, 0 ],
      [ 3, 1 ],
      [ 4, 0 ],
      [ 5, 1 ],
  ]

class CaseDefaultBitsComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= Bits32()
  TV_IN  = _set()
  TV_OUT = _check( 'out', Bits32, 0 )
  TV = \
  [
      [ 0 ],
      [ 0 ],
  ]

#-------------------------------------------------------------------------
# Test cases that contain SystemVerilog translator errors
#-------------------------------------------------------------------------

class CaseVerilogReservedComp:
  class DUT( Component ):
    def construct( s ):
      s.buf = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.buf

class CaseUpdateffMixAssignComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        tmpvar = s.out = Bits32(42)

class CaseInterfaceArrayNonStaticIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ Bits32InIfc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[s.in_[0].foo[0]].foo
  TV_IN = \
  _set(
      'in_[0].foo', Bits32, 0,
      'in_[1].foo', Bits32, 1,
  )
  TV_OUT = \
  _check( 'out', Bits32, 2 )
  TV =\
  [
      [  0,   0,    0 ],
      [  1,   0,    0 ],
      [  1,   1,    1 ],
      [  1,  -1,   -1 ],
      [  1,  42,   42 ],
  ]

#-------------------------------------------------------------------------
# Test cases that contain errors
#-------------------------------------------------------------------------

class CaseStructBitsUnagreeableComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= s.in_

class CaseConcatComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= concat( s, s.in_ )

class CaseZextVaribleNbitsComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= zext( s.in_, s.in_ )

class CaseZextSmallNbitsComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= zext( s.in_, 4 )

class CaseSextVaribleNbitsComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= sext( s.in_, s.in_ )

class CaseSextSmallNbitsComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= sext( s.in_, 4 )

class CaseTruncVaribleNbitsComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= trunc( s.in_, s.in_ )

class CaseTruncLargeNbitsComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= trunc( s.in_, 16 )

class CaseDroppedAttributeComp:
  class DUT( Component ):
    def construct( s ):
      # s.in_ is not recognized by RTLIR and will be dropped
      s.in_ = 'string'
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= s.in_

class CaseL1UnsupportedSubCompAttrComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = [ OutPort( Bits1 ) for _ in range(5) ]
      s.comp_array = [ Bits1OutComp() for _ in range(5) ]
      @update
      def upblk():
        s.out @= s.comp_array[ 0 ].out

class CaseIndexOutOfRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits1 ) for _ in range(4) ]
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[4]

class CaseBitSelOutOfRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[4]

class CaseIndexOnStructComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[16]

class CaseSliceOnStructComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[0:16]

class CaseSliceBoundLowerComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[4:0]

class CaseSliceVariableBoundComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.slice_l = InPort( Bits2 )
      s.slice_r = InPort( Bits2 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[s.slice_l:s.slice_r]

class CaseSliceOutOfRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[0:5]

class CaseLHSConstComp:
  class DUT( Component ):
    def construct( s ):
      u, s.v = 42, 42
      @update
      def upblk():
        s.v @= u

class CaseLHSComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.u = Bits16InOutPassThroughComp()
      @update
      def upblk():
        s.u @= 42

class CaseRHSComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s

class CaseZextOnComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= zext( s, 1 )

class CaseSextOnComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= sext( s, 1 )

class CaseSizeCastComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= Bits32( s )

class CaseAttributeSignalComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.foo

class CaseComponentInIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[ s ]

class CaseComponentBaseIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s[ 1 ]

class CaseComponentLowerSliceComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.idx = Bits16InOutPassThroughComp()
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= s.in_[ s.idx:4 ]

class CaseComponentHigherSliceComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.idx = Bits16InOutPassThroughComp()
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= s.in_[ 0:s.idx ]

class CaseSliceOnComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s[ 0:4 ]

class CaseUpblkArgComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk( number ):
        u = number

class CaseAssignMultiTargetComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        u = v = x = y

class CaseCopyArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        u = copy(42, 10)

class CaseDeepcopyArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        u = deepcopy(42, 10)

class CaseSliceWithStepsComp:
  class DUT( Component ):
    def construct( s ):
      v = 42
      @update
      def upblk():
        u = v[ 0:16:4 ]

class CaseExtendedSubscriptComp:
  class DUT( Component ):
    def construct( s ):
      v = 42
      @update
      def upblk():
        u = v[ 0:8, 16:24 ]

class CaseTmpComponentComp:
  class DUT( Component ):
    def construct( s ):
      v = Bits16InOutPassThroughComp()
      @update
      def upblk():
        u = v

class CaseUntypedTmpComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        u = 42

class CaseStarArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        x = x(*x)

class CaseDoubleStarArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        x = x(**x)

class CaseKwArgsComp:
  class DUT( Component ):
    def construct( s ):
      xx = 42
      @update
      def upblk():
        x = x(x=x)

class CaseNonNameCalledComp:
  class DUT( Component ):
    def construct( s ):
      import copy
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= copy.copy( 42 )

class CaseFuncNotFoundComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        t = undefined_func(u)

class CaseBitsArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        x = Bits32( 42, 42 )

class CaseConcatNoArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        x = concat()

class CaseZextTwoArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        x = zext( s )

class CaseSextTwoArgsComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        x = sext( s )

class CaseUnrecognizedFuncComp:
  class DUT( Component ):
    def construct( s ):
      def foo(): pass
      @update
      def upblk():
        x = foo()

class CaseStandaloneExprComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        42

class CaseLambdaFuncComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= lambda: 42

class CaseDictComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 1:42 }

class CaseSetComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 42 }

class CaseListComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= [ 42 ]

class CaseTupleComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= ( 42, )

class CaseListComprehensionComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= [ 42 for _ in range(1) ]

class CaseSetComprehensionComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 42 for _ in range(1) }

class CaseDictComprehensionComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 1:42 for _ in range(1) }

class CaseGeneratorExprComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= ( 42 for _ in range(1) )

class CaseYieldComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= yield

class CaseReprComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        # Python 2 only: s.out = `42`
        s.out @= repr(42)

class CaseStrComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= '42'

class CaseClassdefComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        class c: pass

class CaseDeleteComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        del u

class CaseWithComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        with u: 42

class CaseRaiseComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        raise 42

class CaseTryExceptComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        try: 42
        except: 42

class CaseTryFinallyComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        try: 42
        finally: 42

class CaseImportComp:
  class DUT( Component ):
    def construct( s ):
      x = 42
      @update
      def upblk():
        import x

class CaseImportFromComp:
  class DUT( Component ):
    def construct( s ):
      x = 42
      @update
      def upblk():
        from x import x

class CaseExecComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        # Python 2 only: exec 42
        exec(42)

class CaseGlobalComp:
  class DUT( Component ):
    def construct( s ):
      u = 42
      @update
      def upblk():
        global u

class CasePassComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        pass

class CaseWhileComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        while 42: 42

class CaseExtSliceComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        42[ 1:2:3, 2:4:6 ]

class CaseAddComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) + s

class CaseInvComponentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= ~s

class CaseComponentStartRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( s, 8, 1 ):
          s.out @= ~Bits1( 1 )

class CaseComponentEndRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, s, 1 ):
          s.out @= ~Bits1( 1 )

class CaseComponentStepRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, 8, s ):
          s.out @= ~Bits1( 1 )

class CaseComponentIfCondComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        if s:
          s.out @= Bits1( 1 )
        else:
          s.out @= ~Bits1( 1 )

class CaseComponentIfExpCondComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if s else ~Bits1(1)

class CaseComponentIfExpBodyComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s if 1 else ~Bits1(1)

class CaseComponentIfExpElseComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if 1 else s

class CaseStructIfCondComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        if s.in_:
          s.out @= Bits1(1)
        else:
          s.out @= ~Bits1(1)

class CaseZeroStepRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, 4, 0 ):
          s.out @= Bits1( 1 )

class CaseVariableStepRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits2 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, 4, s.in_ ):
          s.out @= Bits1( 1 )

class CaseStructIfExpCondComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if s.in_ else ~Bits1(1)

class CaseDifferentTypesIfExpComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if 1 else s.in_

class CaseNotStructComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= ~ s.in_

class CaseAndStructComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) & s.in_

class CaseAddStructBits1Comp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) + s.in_

class CaseExplicitBoolComp:
  class DUT( Component ):
    def construct( s ):
      Bool = rdt.Bool
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bool( Bits1(1) )

class CaseTmpVarUsedBeforeAssignmentComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= u + Bits4( 1 )

class CaseForLoopElseComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range(4):
          s.out @= Bits4( 1 )
        else:
          s.out @= Bits4( 1 )

class CaseSignalAsLoopIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Wire( Bits4 )
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for s.in_ in range(4):
          s.out @= Bits4( 1 )

class CaseRedefLoopIndexComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range(4):
          for i in range(4):
            s.out @= Bits4( 1 )

class CaseSignalAfterInComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits2 )
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in s.in_:
          s.out @= Bits4( 1 )

class CaseFuncCallAfterInComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      def foo(): pass
      @update
      def upblk():
        for i in foo():
          s.out @= Bits4( 1 )

class CaseNoArgsToRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range():
          s.out @= Bits4( 1 )

class CaseTooManyArgsToRangeComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range( 0, 4, 1, 1 ):
          s.out @= Bits4( 1 )

class CaseInvalidIsComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) is Bits1( 1 )

class CaseInvalidIsNotComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) is not Bits1( 1 )

class CaseInvalidInComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) in Bits1( 1 )

class CaseInvalidNotInComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) not in Bits1( 1 )

class CaseInvalidDivComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) // Bits1( 1 )

class CaseMultiOpComparisonComp:
  class DUT( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 0 ) <= Bits2( 1 ) <= Bits2( 2 )

class CaseInvalidBreakComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        for i in range(42): break

class CaseInvalidContinueComp:
  class DUT( Component ):
    def construct( s ):
      @update
      def upblk():
        for i in range(42): continue

class CaseBitsAttributeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_.foo

class CaseStructMissingAttributeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_.bar

class CaseInterfaceMissingAttributeComp:
  class DUT( Component ):
    def construct( s ):
      s.in_ = Bits32OutIfc()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.bar

class CaseSubCompMissingAttributeComp:
  class DUT( Component ):
    def construct( s ):
      s.comp = Bits32OutComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.comp.bar

class CaseCrossHierarchyAccessComp:
  class DUT( Component ):
    def construct( s ):
      s.comp = WrappedBits32OutComp()
      s.a_out = OutPort( Bits32 )
      @update
      def upblk():
        s.a_out @= s.comp.comp.out

class CaseStarArgComp:
  class DUT( Component ):
    def construct( s, *args ):
      pass

class CaseDoubleStarArgComp:
  class DUT( Component ):
    def construct( s, **kwargs ):
      pass
