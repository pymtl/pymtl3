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
  class Bits32PortOnly( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
  DUT = Bits32PortOnly

class CaseStructPortOnly:
  class StructPortOnly( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
  DUT = StructPortOnly

class CaseNestedStructPortOnly:
  class NestedStructPortOnly( Component ):
    def construct( s ):
      s.in_ = InPort( NestedBits32Foo )
  DUT = NestedStructPortOnly

class CasePackedArrayStructPortOnly:
  class PackedArrayStructPortOnly( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
  DUT = PackedArrayStructPortOnly

class CaseBits32x5PortOnly:
  class Bits32x5PortOnly( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
  DUT = Bits32x5PortOnly

class CaseBits32x5WireOnly:
  class Bits32x5WireOnly( Component ):
    def construct( s ):
      s.in_ = [ Wire( Bits32 ) for _ in range(5) ]
  DUT = Bits32x5WireOnly

class CaseStructx5PortOnly:
  class Structx5PortOnly( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32Foo ) for _ in range(5) ]
  DUT = Structx5PortOnly

class CaseBits32x5ConstOnly:
  class Bits32x5ConstOnly( Component ):
    def construct( s ):
      s.in_ = [ Bits32(42) for _ in range(5) ]
  DUT = Bits32x5ConstOnly

class CaseBits32MsgRdyIfcOnly:
  class Bits32MsgRdyIfcOnly( Component ):
    def construct( s ):
      s.in_ = [ Bits32MsgRdyIfc() for _ in range(5) ]
  DUT = Bits32MsgRdyIfcOnly

class CaseBits32InOutx5CompOnly:
  class Bits32InOutx5CompOnly( Component ):
    def construct( s ):
      s.b = [ Bits32InOutComp() for _ in range(5) ]
  DUT = Bits32InOutx5CompOnly

class CaseBits32Outx3x2x1PortOnly:
  class Bits32Outx3x2x1PortOnly( Component ):
    def construct( s ):
      s.out = [[[OutPort(Bits32) for _ in range(1)] for _ in range(2)] for _ in range(3)]
  DUT = Bits32Outx3x2x1PortOnly

class CaseBits32WireIfcOnly:
  class Bits32WireIfcOnly( Component ):
    def construct( s ):
      s.in_ = Bits32FooWireBarInIfc()
  DUT = Bits32WireIfcOnly

class CaseBits32ClosureConstruct:
  class Bits32ClosureConstruct( Component ):
    def construct( s ):
      foo = Bits32( 42 )
      s.fvar_ref = foo
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= foo
  DUT = Bits32ClosureConstruct

class CaseBits32ArrayClosureConstruct:
  class Bits32ArrayClosureConstruct( Component ):
    def construct( s ):
      foo = [ Bits32(42) for _ in range(5) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= foo[2]
  DUT = Bits32ArrayClosureConstruct

class CaseBits32ClosureGlobal:
  class Bits32ClosureGlobal( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= pymtl_Bits_global_freevar
  DUT = Bits32ClosureGlobal

class CaseStructClosureGlobal:
  class StructClosureGlobal( Component ):
    def construct( s ):
      foo = InPort( Bits32Foo )
      s._foo = foo
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= foo.foo
  DUT = StructClosureGlobal

class CaseStructUnique:
  class StructUnique( Component ):
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
  DUT = StructUnique

class CasePythonClassAttr:
  class PythonClassAttr( Component ):
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
  DUT = PythonClassAttr

class CaseTypeBundle:
  class TypeBundle( Component ):
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
  DUT = TypeBundle

class CaseBoolTmpVarComp:
  class BoolTmpVarComp( Component ):
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
  DUT = BoolTmpVarComp

class CaseTmpVarInUpdateffComp:
  class TmpVarInUpdateffComp( Component ):
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
  DUT = TmpVarInUpdateffComp

class CaseBits32FooToBits32Comp:
  class Bits32FooToBits32Comp( Component ):
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
  DUT = Bits32FooToBits32Comp

class CaseBits32ToBits32FooComp:
  class Bits32ToBits32FooComp( Component ):
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
  DUT = Bits32ToBits32FooComp

class CaseIntToBits32FooComp:
  class IntToBits32FooComp( Component ):
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
  DUT = IntToBits32FooComp

class CaseReducesInx3OutComp:
  class ReducesInx3OutComp( Component ):
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
  DUT = ReducesInx3OutComp

class CaseBits16IndexBasicComp:
  class Bits16IndexBasicComp( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits16 ) for _ in range( 4 ) ]
      s.out = [ OutPort( Bits16 ) for _ in range( 2 ) ]
      @update
      def index_basic():
        s.out[ 0 ] @= s.in_[ 0 ] + s.in_[ 1 ]
        s.out[ 1 ] @= s.in_[ 2 ] + s.in_[ 3 ]
  DUT = Bits16IndexBasicComp

class CaseBits8Bits16MismatchAssignComp:
  class Bits8Bits16MismatchAssignComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      @update
      def mismatch_width_assign():
        s.out @= s.in_
  DUT = Bits8Bits16MismatchAssignComp

class CaseBits32Bits64SlicingBasicComp:
  class Bits32Bits64SlicingBasicComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @update
      def slicing_basic():
        s.out[ 0:16 ] @= s.in_[ 16:32 ]
        s.out[ 16:32 ] @= s.in_[ 0:16 ]
  DUT = Bits32Bits64SlicingBasicComp

class CaseBits16ConstAddComp:
  class Bits16ConstAddComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits16 )
      @update
      def bits_basic():
        s.out @= s.in_ + Bits16( 10 )
  DUT = Bits16ConstAddComp

class CaseSlicingOverIndexComp:
  class SlicingOverIndexComp( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits16 ) for _ in range( 10 ) ]
      s.out = [ OutPort( Bits16 ) for _ in range( 5 ) ]
      @update
      def index_bits_slicing():
        s.out[0][0:8] @= s.in_[1][8:16] + s.in_[2][0:8] + 10
        s.out[1] @= s.in_[3][0:16] + s.in_[4] + 1
  DUT = SlicingOverIndexComp

class CaseSubCompAddComp:
  class SubCompAddComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits16 )
      s.b = Bits16InOutPassThroughComp()
      # There should be a way to check module connections?
      connect( s.in_, s.b.in_ )
      @update
      def multi_components_A():
        s.out @= s.in_ + s.b.out
  DUT = SubCompAddComp

class CaseIfBasicComp:
  class IfBasicComp( Component ):
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
  DUT = IfBasicComp

class CaseIfDanglingElseInnerComp:
  class IfDanglingElseInnerComp( Component ):
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
  DUT = IfDanglingElseInnerComp

class CaseIfDanglingElseOutterComp:
  class IfDanglingElseOutterComp( Component ):
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
  DUT = IfDanglingElseOutterComp

class CaseElifBranchComp:
  class ElifBranchComp( Component ):
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
  DUT = ElifBranchComp

class CaseNestedIfComp:
  class NestedIfComp( Component ):
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
  DUT = NestedIfComp

class CaseForBasicComp:
  class ForBasicComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      @update
      def for_basic():
        for i in range( 8 ):
          s.out[ 2*i:2*i+1 ] @= s.in_[ 2*i:2*i+1 ] + s.in_[ 2*i+1:(2*i+1)+1 ]
  DUT = ForBasicComp

class CaseForFreeVarStepComp:
  class ForFreeVarStepComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = OutPort( Bits8 )
      freevar = 1
      @update
      def upblk():
        for i in range( 0, 2, freevar ):
          s.out @= s.in_[0:8]
  DUT = ForFreeVarStepComp

class CaseTypeNameAsFieldNameComp:
  class TypeNameAsFieldNameComp( Component ):
    def construct( s ):
      s.in_ = InPort( StructTypeNameAsFieldName )
      s.out = OutPort( StructTypeNameAsFieldName )
      s.in_ //= s.out
  DUT = TypeNameAsFieldNameComp

class CaseForRangeLowerUpperStepPassThroughComp:
  class ForRangeLowerUpperStepPassThroughComp( Component ):
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
  DUT = ForRangeLowerUpperStepPassThroughComp

class CaseForLoopEmptySequenceComp:
  class ForLoopEmptySequenceComp( Component ):
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
  DUT = ForLoopEmptySequenceComp

class CaseIfExpBothImplicitComp:
  class IfExpBothImplicitComp( Component ):
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
  DUT = IfExpBothImplicitComp

class CaseIfExpInForStmtComp:
  class IfExpInForStmtComp( Component ):
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
  DUT = IfExpInForStmtComp

class CaseIfExpUnaryOpInForStmtComp:
  class IfExpUnaryOpInForStmtComp( Component ):
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
  DUT = IfExpUnaryOpInForStmtComp

class CaseIfBoolOpInForStmtComp:
  class IfBoolOpInForStmtComp( Component ):
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
  DUT = IfBoolOpInForStmtComp

class CaseIfTmpVarInForStmtComp:
  class IfTmpVarInForStmtComp( Component ):
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
  DUT = IfTmpVarInForStmtComp

class CaseFixedSizeSliceComp:
  class FixedSizeSliceComp( Component ):
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
  DUT = FixedSizeSliceComp

class CaseTwoUpblksSliceComp:
  class TwoUpblksSliceComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits8 )
      @update
      def multi_upblks_1():
        s.out[ 0:4 ] @= s.in_
      @update
      def multi_upblks_2():
        s.out[ 4:8 ] @= s.in_
  DUT = TwoUpblksSliceComp

class CaseTwoUpblksFreevarsComp:
  class TwoUpblksFreevarsComp( Component ):
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
  DUT = TwoUpblksFreevarsComp

class CaseTwoUpblksStructTmpWireComp:
  class TwoUpblksStructTmpWireComp( Component ):
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
  DUT = TwoUpblksStructTmpWireComp

class CaseFlipFlopAdder:
  class FlipFlopAdder( Component ):
    def construct( s ):
      s.in0 = InPort( Bits32 )
      s.in1 = InPort( Bits32 )
      s.out0 = OutPort( Bits32 )
      @update_ff
      def update_ff_upblk():
        s.out0 <<= s.in0 + s.in1
  DUT = FlipFlopAdder

class CaseConstSizeSlicingComp:
  class ConstSizeSlicingComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits16 )
      s.out = [ OutPort( Bits8 ) for _ in range(2) ]
      @update
      def upblk():
        for i in range(2):
          s.out[i] @= s.in_[i*8 : i*8 + 8]
  DUT = ConstSizeSlicingComp

class CaseBits32TmpWireComp:
  class Bits32TmpWireComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_ + 42
        s.out @= u
  DUT = Bits32TmpWireComp

class CaseBits32MultiTmpWireComp:
  class Bits32MultiTmpWireComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_ + 42
        v = s.in_ + 40
        s.out @= u
        s.out @= v
  DUT = Bits32MultiTmpWireComp

class CaseBits32FreeVarToTmpVarComp:
  class Bits32FreeVarToTmpVarComp( Component ):
    def construct( s ):
      # STATE_IDLE = Bits32(0)
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = STATE_IDLE
        s.out @= u
  DUT = Bits32FreeVarToTmpVarComp

class CaseBits32ConstBitsToTmpVarComp:
  class Bits32ConstBitsToTmpVarComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = Bits32(0)
        s.out @= u
  DUT = Bits32ConstBitsToTmpVarComp

class CaseBits32ConstIntToTmpVarComp:
  class Bits32ConstIntToTmpVarComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = 1
        s.out @= u
  DUT = Bits32ConstIntToTmpVarComp

class CaseBits32TmpWireAliasComp:
  class Bits32TmpWireAliasComp( Component ):
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
  DUT = Bits32TmpWireAliasComp

class CaseStructTmpWireComp:
  class StructTmpWireComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_
        s.out @= u.foo
  DUT = StructTmpWireComp

class CaseTmpWireOverwriteConflictComp:
  class TmpWireOverwriteConflictComp( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits16 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.in_1 + 42
        u = s.in_2 + 1
        s.out @= u
  DUT = TmpWireOverwriteConflictComp

class CaseScopeTmpWireOverwriteConflictComp:
  class ScopeTmpWireOverwriteConflictComp( Component ):
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
  DUT = ScopeTmpWireOverwriteConflictComp

class CaseHeteroCompArrayComp:
  class HeteroCompArrayComp( Component ):
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
  DUT = HeteroCompArrayComp

class CaseChildExplicitModuleName:
  class ChildExplicitModuleName( Component ):
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
  DUT = ChildExplicitModuleName

#-------------------------------------------------------------------------
# Test cases without errors
#-------------------------------------------------------------------------

class CaseSizeCastPaddingStructPort:
  class SizeCastPaddingStructPort( Component ):
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
  DUT = SizeCastPaddingStructPort

class CaseBits32x2ConcatComp:
  class Bits32x2ConcatComp( Component ):
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
  DUT = Bits32x2ConcatComp

class CaseBits32x2ConcatConstComp:
  class Bits32x2ConcatConstComp( Component ):
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
  DUT = Bits32x2ConcatConstComp

class CaseBits32x2ConcatMixedComp:
  class Bits32x2ConcatMixedComp( Component ):
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
  DUT = Bits32x2ConcatMixedComp

class CaseBits32x2ConcatFreeVarComp:
  class Bits32x2ConcatFreeVarComp( Component ):
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
  DUT = Bits32x2ConcatFreeVarComp

class CaseBits32x2ConcatUnpackedSignalComp:
  class Bits32x2ConcatUnpackedSignalComp( Component ):
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
  DUT = Bits32x2ConcatUnpackedSignalComp

class CaseBits64SextInComp:
  class Bits64SextInComp( Component ):
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
  DUT = Bits64SextInComp

class CaseBits64ZextInComp:
  class Bits64ZextInComp( Component ):
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
  DUT = Bits64ZextInComp

class CaseBits64TruncInComp:
  class Bits64TruncInComp( Component ):
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
  DUT = Bits64TruncInComp

class CaseBits32BitSelUpblkComp:
  class Bits32BitSelUpblkComp( Component ):
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
  DUT = Bits32BitSelUpblkComp

class CaseBits64PartSelUpblkComp:
  class Bits64PartSelUpblkComp( Component ):
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
  DUT = Bits64PartSelUpblkComp

class CasePassThroughComp:
  class PassThroughComp( Component ):
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
  DUT = PassThroughComp

class CaseSequentialPassThroughComp:
  class SequentialPassThroughComp( Component ):
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
  DUT = SequentialPassThroughComp

class CaseConnectPassThroughLongNameComp:
  class ConnectPassThroughLongNameComp( Component ):
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
  DUT = ConnectPassThroughLongNameComp

class CaseLambdaConnectComp:
  class LambdaConnectComp( Component ):
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
  DUT = LambdaConnectComp

class CaseLambdaConnectWithListComp:
  class LambdaConnectWithListComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = [ OutPort( Bits32 ) for _ in range(2) ]
      s.out[1] //= lambda: s.in_ + 42
  DUT = LambdaConnectWithListComp

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
  class Bits32FooInBits32OutComp( Component ):
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
  DUT = Bits32FooInBits32OutComp

class CaseBits32FooKwargComp:
  class Bits32FooKwargComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= Bits32Foo( foo = 42 )
  DUT = Bits32FooKwargComp

class CaseBits32FooInstantiationComp:
  class Bits32FooInstantiationComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32Foo )
      @update
      def upblk():
        s.out @= Bits32Foo( 42 )
  DUT = Bits32FooInstantiationComp

class CaseConstStructInstComp:
  class ConstStructInstComp( Component ):
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
  DUT = ConstStructInstComp

class CaseStructPackedArrayUpblkComp:
  class StructPackedArrayUpblkComp( Component ):
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
  DUT = StructPackedArrayUpblkComp

class CaseConnectLiteralStructComp:
  class ConnectLiteralStructComp( Component ):
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
  DUT = ConnectLiteralStructComp

class CaseNestedStructPackedArrayUpblkComp:
  class NestedStructPackedArrayUpblkComp( Component ):
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
  DUT = NestedStructPackedArrayUpblkComp

class CaseConnectNestedStructPackedArrayComp:
  class ConnectNestedStructPackedArrayComp( Component ):
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
  DUT = ConnectNestedStructPackedArrayComp

class CaseInterfaceAttributeComp:
  class InterfaceAttributeComp( Component ):
    def construct( s ):
      s.in_ = Bits32OutIfc()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.foo
  DUT = InterfaceAttributeComp

class CaseArrayInterfacesComp:
  class ArrayInterfacesComp( Component ):
    def construct( s ):
      s.in_ = [ Bits32OutIfc() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[2].foo
  DUT = ArrayInterfacesComp

class CaseBits32SubCompPassThroughComp:
  class Bits32SubCompPassThroughComp( Component ):
    def construct( s ):
      s.comp = Bits32OutComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.comp.out
  DUT = Bits32SubCompPassThroughComp

class CaseArrayBits32SubCompPassThroughComp:
  class ArrayBits32SubCompPassThroughComp( Component ):
    def construct( s ):
      s.comp = [ Bits32OutComp() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.comp[2].out
  DUT = ArrayBits32SubCompPassThroughComp

class CaseSubCompTmpDrivenComp:
  class SubCompTmpDrivenComp( Component ):
    def construct( s ):
      s.subcomp = Bits32OutTmpDrivenComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        u = s.subcomp.out
        s.out @= u
  DUT = SubCompTmpDrivenComp

class CaseSubCompFreeVarDrivenComp:
  class SubCompFreeVarDrivenComp( Component ):
    def construct( s ):
      s.subcomp = Bits32OutFreeVarDrivenComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        if 1:
          s.out @= s.subcomp.out
        else:
          s.out @= STATE_IDLE
  DUT = SubCompFreeVarDrivenComp

class CaseConstBits32AttrComp:
  class ConstBits32AttrComp( Component ):
    def construct( s ):
      s.const = [ Bits32(42) for _ in range(5) ]
  DUT = ConstBits32AttrComp

class CaseInx2Outx2ConnectComp:
  class Inx2Outx2ConnectComp( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out1 = OutPort( Bits32 )
      s.out2 = OutPort( Bits32 )
      connect( s.in_1, s.out1 )
      connect( s.in_2, s.out2 )
  DUT = Inx2Outx2ConnectComp

class CaseConnectPortIndexComp:
  class ConnectPortIndexComp( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = OutPort( Bits32 )
      connect( s.in_[2], s.out )
  DUT = ConnectPortIndexComp

class CaseConnectInToWireComp:
  class ConnectInToWireComp( Component ):
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
  DUT = ConnectInToWireComp

class CaseWiresDrivenComp:
  class WiresDrivenComp( Component ):
    def construct( s ):
      s.foo = Wire( Bits32 )
      s.bar = Wire( Bits4 )
      @update
      def upblk():
        s.foo @= 42
        s.bar @= 0
  DUT = WiresDrivenComp

class CaseBits32Wirex5DrivenComp:
  class Bits32Wirex5DrivenComp( Component ):
    def construct( s ):
      s.foo = [ Wire( Bits32 ) for _ in range(5) ]
      @update
      def upblk():
        for i in range(5):
          s.foo[i] @= 0
  DUT = Bits32Wirex5DrivenComp

class CaseStructWireDrivenComp:
  class StructWireDrivenComp( Component ):
    def construct( s ):
      s.foo = Wire( Bits32Foo )
      @update
      def upblk():
        s.foo.foo @= 42
  DUT = StructWireDrivenComp

class CaseStructConstComp:
  class StructConstComp( Component ):
    def construct( s ):
      s.struct_const = Bits32Foo()
  DUT = StructConstComp

class CaseNestedPackedArrayStructComp:
  class NestedPackedArrayStructComp( Component ):
    def construct( s ):
      s.in_ = InPort( NestedStructPackedArray )
      s.out = OutPort( Bits32x5Foo )
      connect( s.in_.foo[1], s.out )
  DUT = NestedPackedArrayStructComp

class CaseConnectConstToOutComp:
  class ConnectConstToOutComp( Component ):
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
  DUT = ConnectConstToOutComp

class CaseConnectBitSelToOutComp:
  class ConnectBitSelToOutComp( Component ):
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
  DUT = ConnectBitSelToOutComp

class CaseConnectSliceToOutComp:
  class ConnectSliceToOutComp( Component ):
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
  DUT = ConnectSliceToOutComp

class CaseConnectBitsConstToOutComp:
  class ConnectBitsConstToOutComp( Component ):
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
  DUT = ConnectBitsConstToOutComp

class CaseConnectStructAttrToOutComp:
  class ConnectStructAttrToOutComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
  DUT = ConnectStructAttrToOutComp

class CaseConnectArrayStructAttrToOutComp:
  class ConnectArrayStructAttrToOutComp( Component ):
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
  DUT = ConnectArrayStructAttrToOutComp

class CaseConnectConstStructAttrToOutComp:
  class ConnectConstStructAttrToOutComp( Component ):
    def construct( s ):
      s.in_ = Bits32Foo( 42 )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =[ [ 42 ] ]
  DUT = ConnectConstStructAttrToOutComp

class CaseBits32IfcInComp:
  class Bits32IfcInComp( Component ):
    def construct( s ):
      s.in_ = Bits32InIfc()
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
  DUT = Bits32IfcInComp

class CaseArrayBits32IfcInComp:
  class ArrayBits32IfcInComp( Component ):
    def construct( s ):
      s.in_ = [ Bits32InIfc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      connect( s.in_[1].foo, s.out )
  DUT = ArrayBits32IfcInComp

class CaseBits32FooNoArgBehavioralComp:
  class Bits32FooNoArgBehavioralComp( Component ):
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
  DUT = Bits32FooNoArgBehavioralComp

class CaseArrayBits32IfcInUpblkComp:
  class ArrayBits32IfcInUpblkComp( Component ):
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
  DUT = ArrayBits32IfcInUpblkComp

class CaseConnectValRdyIfcComp:
  class ConnectValRdyIfcComp( Component ):
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
  DUT = ConnectValRdyIfcComp

class CaseConnectValRdyIfcUpblkComp:
  class ConnectValRdyIfcUpblkComp( Component ):
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
  DUT = ConnectValRdyIfcUpblkComp

class CaseConnectArrayBits32FooIfcComp:
  class ConnectArrayBits32FooIfcComp( Component ):
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
  DUT = ConnectArrayBits32FooIfcComp

class CaseConnectArrayBits32Comp:
  class ConnectArrayBits32Comp( Component ):
    def construct( s ):
      s.in_ = [ InPort(32) for _ in range(2) ]
      s.out = [ OutPort(32) for _ in range(2) ]
      for i in range(2):
        connect( s.out[i], s.in_[i] )
  TV_IN = \
  _set(
      'in_[0]',   Bits32,  0,
      'in_[1]',   Bits32,  1,
  )
  TV_OUT = \
  _check(
      'out[0]',   Bits32,  2,
      'out[1]',   Bits32,  3,
  )
  TV =\
  [
      [ 1,      0,    1,      0, ],
      [ 0,     42,    0,     42, ],
      [ 1,     42,    1,     42, ],
      [ 1,     -1,    1,     -1, ],
      [ 1,     -2,    1,     -2, ],
  ]
  DUT = ConnectArrayBits32Comp

class CaseConnectArrayNestedIfcComp:
  class ConnectArrayNestedIfcComp( Component ):
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
  DUT = ConnectArrayNestedIfcComp

class CaseBits32IfcTmpVarOutComp:
  class Bits32IfcTmpVarOutComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.ifc = Bits32OutIfc()
      @update
      def upblk():
        u = s.ifc.foo
        s.out @= u
  DUT = Bits32IfcTmpVarOutComp

class CaseStructIfcTmpVarOutComp:
  class StructIfcTmpVarOutComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.ifc = Bits32FooInIfc()
      @update
      def upblk():
        u = s.ifc.foo
        s.out @= u.foo
  DUT = StructIfcTmpVarOutComp

class CaseBits32ConnectSubCompAttrComp:
  class Bits32ConnectSubCompAttrComp( Component ):
    def construct( s ):
      s.b = Bits32OutDrivenComp()
      s.out = OutPort( Bits32 )
      connect( s.out, s.b.out )
  TV_IN = \
  _set()
  TV_OUT = \
  _check( 'out', Bits32, 0 )
  TV =[ [ 42 ] ]
  DUT = Bits32ConnectSubCompAttrComp

class CaseBits32SubCompAttrUpblkComp:
  class Bits32SubCompAttrUpblkComp( Component ):
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
  DUT = Bits32SubCompAttrUpblkComp

class CaseConnectSubCompIfcHierarchyComp:
  class ConnectSubCompIfcHierarchyComp( Component ):
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
  DUT = ConnectSubCompIfcHierarchyComp

class CaseConnectArraySubCompArrayStructIfcComp:
  class ConnectArraySubCompArrayStructIfcComp( Component ):
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
  DUT = ConnectArraySubCompArrayStructIfcComp

class CaseBehavioralArraySubCompArrayStructIfcComp:
  class BehavioralArraySubCompArrayStructIfcComp( Component ):
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
  DUT = BehavioralArraySubCompArrayStructIfcComp

class CaseBits32ArrayConnectSubCompAttrComp:
  class Bits32ArrayConnectSubCompAttrComp( Component ):
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
  DUT = Bits32ArrayConnectSubCompAttrComp

class CaseBits32ArraySubCompAttrUpblkComp:
  class Bits32ArraySubCompAttrUpblkComp( Component ):
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
  DUT = Bits32ArraySubCompAttrUpblkComp

class CaseComponentArgsComp:
  class ComponentArgsComp( Component ):
    def construct( s, foo, bar ):
      pass
  DUT = ComponentArgsComp

class CaseComponentDefaultArgsComp:
  class ComponentDefaultArgsComp( Component ):
    def construct( s, foo, bar = Bits16(42) ):
      pass
  DUT = ComponentDefaultArgsComp

class CaseMixedDefaultArgsComp:
  class MixedDefaultArgsComp( Component ):
    def construct( s, foo, bar, woo = Bits32(0) ):
      pass
  DUT = MixedDefaultArgsComp

class CaseGenericAdderComp:
  class GenericAdderComp( Component ):
    def construct( s, Type ):
      s.in_1 = InPort( Type )
      s.in_2 = InPort( Type )
      s.out = OutPort( Type )
      @update
      def add_upblk():
        s.out @= s.in_1 + s.in_2
    def line_trace( s ): return 'sum = ' + str(s.out)
  DUT = GenericAdderComp

class CaseGenericMuxComp:
  class GenericMuxComp( Component ):
    def construct( s, Type, n_ports ):
      s.in_ = [ InPort( Type ) for _ in range(n_ports) ]
      s.sel = InPort( mk_bits( clog2(n_ports) ) )
      s.out = OutPort( Type )
      @update
      def add_upblk():
        s.out @= s.in_[ s.sel ]
    def line_trace( s ): return "out = " + str( s.out )
  DUT = GenericMuxComp

class CaseStructConnectWireComp:
  class StructConnectWireComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
    def line_trace( s ): return "out = " + str( s.out )
  DUT = StructConnectWireComp

class CaseNestedStructConnectWireComp:
  class NestedStructConnectWireComp( Component ):
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
  DUT = NestedStructConnectWireComp

class CaseNestedStructConnectWireSubComp:
  class NestedStructConnectWireSubComp( Component ):
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
  DUT = NestedStructConnectWireSubComp

class CaseGenericConditionalDriveComp:
  class GenericConditionalDriveComp( Component ):
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
  DUT = GenericConditionalDriveComp

class CaseBitSelOverBitSelComp:
  class BitSelOverBitSelComp( Component ):
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
  DUT = BitSelOverBitSelComp

class CaseBitSelOverPartSelComp:
  class BitSelOverPartSelComp( Component ):
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
  DUT = BitSelOverPartSelComp

class CasePartSelOverBitSelComp:
  class PartSelOverBitSelComp( Component ):
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
  DUT = PartSelOverBitSelComp

class CasePartSelOverPartSelComp:
  class PartSelOverPartSelComp( Component ):
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
  DUT = PartSelOverPartSelComp

class CaseDefaultBitsComp:
  class DefaultBitsComp( Component ):
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
  DUT = DefaultBitsComp

#-------------------------------------------------------------------------
# Test cases that contain SystemVerilog translator errors
#-------------------------------------------------------------------------

class CaseVerilogReservedComp:
  class VerilogReservedComp( Component ):
    def construct( s ):
      s.buf = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.buf
  DUT = VerilogReservedComp

class CaseUpdateffMixAssignComp:
  class UpdateffMixAssignComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        tmpvar = s.out = Bits32(42)
  DUT = UpdateffMixAssignComp

class CaseInterfaceArrayNonStaticIndexComp:
  class InterfaceArrayNonStaticIndexComp( Component ):
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
  DUT = InterfaceArrayNonStaticIndexComp

#-------------------------------------------------------------------------
# Test cases that contain errors
#-------------------------------------------------------------------------

class CaseStructBitsUnagreeableComp:
  class StructBitsUnagreeableComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= s.in_
  DUT = StructBitsUnagreeableComp

class CaseConcatComponentComp:
  class ConcatComponentComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= concat( s, s.in_ )
  DUT = ConcatComponentComp

class CaseZextVaribleNbitsComp:
  class ZextVaribleNbitsComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= zext( s.in_, s.in_ )
  DUT = ZextVaribleNbitsComp

class CaseZextSmallNbitsComp:
  class ZextSmallNbitsComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= zext( s.in_, 4 )
  DUT = ZextSmallNbitsComp

class CaseSextVaribleNbitsComp:
  class SextVaribleNbitsComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= sext( s.in_, s.in_ )
  DUT = SextVaribleNbitsComp

class CaseSextSmallNbitsComp:
  class SextSmallNbitsComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= sext( s.in_, 4 )
  DUT = SextSmallNbitsComp

class CaseTruncVaribleNbitsComp:
  class TruncVaribleNbitsComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= trunc( s.in_, s.in_ )
  DUT = TruncVaribleNbitsComp

class CaseTruncLargeNbitsComp:
  class TruncLargeNbitsComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits8 )
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= trunc( s.in_, 16 )
  DUT = TruncLargeNbitsComp

class CaseDroppedAttributeComp:
  class DroppedAttributeComp( Component ):
    def construct( s ):
      # s.in_ is not recognized by RTLIR and will be dropped
      s.in_ = 'string'
      s.out = OutPort( Bits16 )
      @update
      def upblk():
        s.out @= s.in_
  DUT = DroppedAttributeComp

class CaseL1UnsupportedSubCompAttrComp:
  class L1UnsupportedSubCompAttrComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = [ OutPort( Bits1 ) for _ in range(5) ]
      s.comp_array = [ Bits1OutComp() for _ in range(5) ]
      @update
      def upblk():
        s.out @= s.comp_array[ 0 ].out
  DUT = L1UnsupportedSubCompAttrComp

class CaseIndexOutOfRangeComp:
  class IndexOutOfRangeComp( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits1 ) for _ in range(4) ]
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[4]
  DUT = IndexOutOfRangeComp

class CaseBitSelOutOfRangeComp:
  class BitSelOutOfRangeComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[4]
  DUT = BitSelOutOfRangeComp

class CaseIndexOnStructComp:
  class IndexOnStructComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[16]
  DUT = IndexOnStructComp

class CaseSliceOnStructComp:
  class SliceOnStructComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32x5Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[0:16]
  DUT = SliceOnStructComp

class CaseSliceBoundLowerComp:
  class SliceBoundLowerComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[4:0]
  DUT = SliceBoundLowerComp

class CaseSliceVariableBoundComp:
  class SliceVariableBoundComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.slice_l = InPort( Bits2 )
      s.slice_r = InPort( Bits2 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[s.slice_l:s.slice_r]
  DUT = SliceVariableBoundComp

class CaseSliceOutOfRangeComp:
  class SliceOutOfRangeComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits4 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_[0:5]
  DUT = SliceOutOfRangeComp

class CaseLHSConstComp:
  class LHSConstComp( Component ):
    def construct( s ):
      u, s.v = 42, 42
      @update
      def upblk():
        s.v @= u
  DUT = LHSConstComp

class CaseLHSComponentComp:
  class LHSComponentComp( Component ):
    def construct( s ):
      s.u = Bits16InOutPassThroughComp()
      @update
      def upblk():
        s.u @= 42
  DUT = LHSComponentComp

class CaseRHSComponentComp:
  class RHSComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s
  DUT = RHSComponentComp

class CaseZextOnComponentComp:
  class ZextOnComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= zext( s, 1 )
  DUT = ZextOnComponentComp

class CaseSextOnComponentComp:
  class SextOnComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= sext( s, 1 )
  DUT = SextOnComponentComp

class CaseSizeCastComponentComp:
  class SizeCastComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= Bits32( s )
  DUT = SizeCastComponentComp

class CaseAttributeSignalComp:
  class AttributeSignalComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.foo
  DUT = AttributeSignalComp

class CaseComponentInIndexComp:
  class ComponentInIndexComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_[ s ]
  DUT = ComponentInIndexComp

class CaseComponentBaseIndexComp:
  class ComponentBaseIndexComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s[ 1 ]
  DUT = ComponentBaseIndexComp

class CaseComponentLowerSliceComp:
  class ComponentLowerSliceComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.idx = Bits16InOutPassThroughComp()
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= s.in_[ s.idx:4 ]
  DUT = ComponentLowerSliceComp

class CaseComponentHigherSliceComp:
  class ComponentHigherSliceComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.idx = Bits16InOutPassThroughComp()
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= s.in_[ 0:s.idx ]
  DUT = ComponentHigherSliceComp

class CaseSliceOnComponentComp:
  class SliceOnComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s[ 0:4 ]
  DUT = SliceOnComponentComp

class CaseUpblkArgComp:
  class UpblkArgComp( Component ):
    def construct( s ):
      @update
      def upblk( number ):
        u = number
  DUT = UpblkArgComp

class CaseAssignMultiTargetComp:
  class AssignMultiTargetComp( Component ):
    def construct( s ):
      @update
      def upblk():
        u = v = x = y
  DUT = AssignMultiTargetComp

class CaseCopyArgsComp:
  class CopyArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        u = copy(42, 10)
  DUT = CopyArgsComp

class CaseDeepcopyArgsComp:
  class DeepcopyArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        u = deepcopy(42, 10)
  DUT = DeepcopyArgsComp

class CaseSliceWithStepsComp:
  class SliceWithStepsComp( Component ):
    def construct( s ):
      v = 42
      @update
      def upblk():
        u = v[ 0:16:4 ]
  DUT = SliceWithStepsComp

class CaseExtendedSubscriptComp:
  class ExtendedSubscriptComp( Component ):
    def construct( s ):
      v = 42
      @update
      def upblk():
        u = v[ 0:8, 16:24 ]
  DUT = ExtendedSubscriptComp

class CaseTmpComponentComp:
  class TmpComponentComp( Component ):
    def construct( s ):
      v = Bits16InOutPassThroughComp()
      @update
      def upblk():
        u = v
  DUT = TmpComponentComp

class CaseUntypedTmpComp:
  class UntypedTmpComp( Component ):
    def construct( s ):
      @update
      def upblk():
        u = 42
  DUT = UntypedTmpComp

class CaseStarArgsComp:
  class StarArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        x = x(*x)
  DUT = StarArgsComp

class CaseDoubleStarArgsComp:
  class DoubleStarArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        x = x(**x)
  DUT = DoubleStarArgsComp

class CaseKwArgsComp:
  class KwArgsComp( Component ):
    def construct( s ):
      xx = 42
      @update
      def upblk():
        x = x(x=x)
  DUT = KwArgsComp

class CaseNonNameCalledComp:
  class NonNameCalledComp( Component ):
    def construct( s ):
      import copy
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= copy.copy( 42 )
  DUT = NonNameCalledComp

class CaseFuncNotFoundComp:
  class FuncNotFoundComp( Component ):
    def construct( s ):
      @update
      def upblk():
        t = undefined_func(u)
  DUT = FuncNotFoundComp

class CaseBitsArgsComp:
  class BitsArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        x = Bits32( 42, 42 )
  DUT = BitsArgsComp

class CaseConcatNoArgsComp:
  class ConcatNoArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        x = concat()
  DUT = ConcatNoArgsComp

class CaseZextTwoArgsComp:
  class ZextTwoArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        x = zext( s )
  DUT = ZextTwoArgsComp

class CaseSextTwoArgsComp:
  class SextTwoArgsComp( Component ):
    def construct( s ):
      @update
      def upblk():
        x = sext( s )
  DUT = SextTwoArgsComp

class CaseUnrecognizedFuncComp:
  class UnrecognizedFuncComp( Component ):
    def construct( s ):
      def foo(): pass
      @update
      def upblk():
        x = foo()
  DUT = UnrecognizedFuncComp

class CaseStandaloneExprComp:
  class StandaloneExprComp( Component ):
    def construct( s ):
      @update
      def upblk():
        42
  DUT = StandaloneExprComp

class CaseLambdaFuncComp:
  class LambdaFuncComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= lambda: 42
  DUT = LambdaFuncComp

class CaseDictComp:
  class DictComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 1:42 }
  DUT = DictComp

class CaseSetComp:
  class SetComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 42 }
  DUT = SetComp

class CaseListComp:
  class ListComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= [ 42 ]
  DUT = ListComp

class CaseTupleComp:
  class TupleComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= ( 42, )
  DUT = TupleComp

class CaseListComprehensionComp:
  class ListComprehensionComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= [ 42 for _ in range(1) ]
  DUT = ListComprehensionComp

class CaseSetComprehensionComp:
  class SetComprehensionComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 42 for _ in range(1) }
  DUT = SetComprehensionComp

class CaseDictComprehensionComp:
  class DictComprehensionComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= { 1:42 for _ in range(1) }
  DUT = DictComprehensionComp

class CaseGeneratorExprComp:
  class GeneratorExprComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= ( 42 for _ in range(1) )
  DUT = GeneratorExprComp

class CaseYieldComp:
  class YieldComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= yield
  DUT = YieldComp

class CaseReprComp:
  class ReprComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        # Python 2 only: s.out = `42`
        s.out @= repr(42)
  DUT = ReprComp

class CaseStrComp:
  class StrComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= '42'
  DUT = StrComp

class CaseClassdefComp:
  class ClassdefComp( Component ):
    def construct( s ):
      @update
      def upblk():
        class c: pass
  DUT = ClassdefComp

class CaseDeleteComp:
  class DeleteComp( Component ):
    def construct( s ):
      @update
      def upblk():
        del u
  DUT = DeleteComp

class CaseWithComp:
  class WithComp( Component ):
    def construct( s ):
      @update
      def upblk():
        with u: 42
  DUT = WithComp

class CaseRaiseComp:
  class RaiseComp( Component ):
    def construct( s ):
      @update
      def upblk():
        raise 42
  DUT = RaiseComp

class CaseTryExceptComp:
  class TryExceptComp( Component ):
    def construct( s ):
      @update
      def upblk():
        try: 42
        except: 42
  DUT = TryExceptComp

class CaseTryFinallyComp:
  class TryFinallyComp( Component ):
    def construct( s ):
      @update
      def upblk():
        try: 42
        finally: 42
  DUT = TryFinallyComp

class CaseImportComp:
  class ImportComp( Component ):
    def construct( s ):
      x = 42
      @update
      def upblk():
        import x
  DUT = ImportComp

class CaseImportFromComp:
  class ImportFromComp( Component ):
    def construct( s ):
      x = 42
      @update
      def upblk():
        from x import x
  DUT = ImportFromComp

class CaseExecComp:
  class ExecComp( Component ):
    def construct( s ):
      @update
      def upblk():
        # Python 2 only: exec 42
        exec(42)
  DUT = ExecComp

class CaseGlobalComp:
  class GlobalComp( Component ):
    def construct( s ):
      u = 42
      @update
      def upblk():
        global u
  DUT = GlobalComp

class CasePassComp:
  class PassComp( Component ):
    def construct( s ):
      @update
      def upblk():
        pass
  DUT = PassComp

class CaseWhileComp:
  class WhileComp( Component ):
    def construct( s ):
      @update
      def upblk():
        while 42: 42
  DUT = WhileComp

class CaseExtSliceComp:
  class ExtSliceComp( Component ):
    def construct( s ):
      @update
      def upblk():
        a = None
        a[ 1:2:3, 2:4:6 ]
  DUT = ExtSliceComp

class CaseAddComponentComp:
  class AddComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) + s
  DUT = AddComponentComp

class CaseInvComponentComp:
  class InvComponentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= ~s
  DUT = InvComponentComp

class CaseComponentStartRangeComp:
  class ComponentStartRangeComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( s, 8, 1 ):
          s.out @= ~Bits1( 1 )
  DUT = ComponentStartRangeComp

class CaseComponentEndRangeComp:
  class ComponentEndRangeComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, s, 1 ):
          s.out @= ~Bits1( 1 )
  DUT = ComponentEndRangeComp

class CaseComponentStepRangeComp:
  class ComponentStepRangeComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, 8, s ):
          s.out @= ~Bits1( 1 )
  DUT = ComponentStepRangeComp

class CaseComponentIfCondComp:
  class ComponentIfCondComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        if s:
          s.out @= Bits1( 1 )
        else:
          s.out @= ~Bits1( 1 )
  DUT = ComponentIfCondComp

class CaseComponentIfExpCondComp:
  class ComponentIfExpCondComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if s else ~Bits1(1)
  DUT = ComponentIfExpCondComp

class CaseComponentIfExpBodyComp:
  class ComponentIfExpBodyComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s if 1 else ~Bits1(1)
  DUT = ComponentIfExpBodyComp

class CaseComponentIfExpElseComp:
  class ComponentIfExpElseComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if 1 else s
  DUT = ComponentIfExpElseComp

class CaseStructIfCondComp:
  class StructIfCondComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        if s.in_:
          s.out @= Bits1(1)
        else:
          s.out @= ~Bits1(1)
  DUT = StructIfCondComp

class CaseZeroStepRangeComp:
  class ZeroStepRangeComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, 4, 0 ):
          s.out @= Bits1( 1 )
  DUT = ZeroStepRangeComp

class CaseVariableStepRangeComp:
  class VariableStepRangeComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits2 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        for i in range( 0, 4, s.in_ ):
          s.out @= Bits1( 1 )
  DUT = VariableStepRangeComp

class CaseStructIfExpCondComp:
  class StructIfExpCondComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if s.in_ else ~Bits1(1)
  DUT = StructIfExpCondComp

class CaseDifferentTypesIfExpComp:
  class DifferentTypesIfExpComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1(1) if 1 else s.in_
  DUT = DifferentTypesIfExpComp

class CaseNotStructComp:
  class NotStructComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= ~ s.in_
  DUT = NotStructComp

class CaseAndStructComp:
  class AndStructComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) & s.in_
  DUT = AndStructComp

class CaseAddStructBits1Comp:
  class AddStructBits1Comp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) + s.in_
  DUT = AddStructBits1Comp

class CaseExplicitBoolComp:
  class ExplicitBoolComp( Component ):
    def construct( s ):
      Bool = rdt.Bool
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= Bool( Bits1(1) )
  DUT = ExplicitBoolComp

class CaseTmpVarUsedBeforeAssignmentComp:
  class TmpVarUsedBeforeAssignmentComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= u + Bits4( 1 )
  DUT = TmpVarUsedBeforeAssignmentComp

class CaseForLoopElseComp:
  class ForLoopElseComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range(4):
          s.out @= Bits4( 1 )
        else:
          s.out @= Bits4( 1 )
  DUT = ForLoopElseComp

class CaseSignalAsLoopIndexComp:
  class SignalAsLoopIndexComp( Component ):
    def construct( s ):
      s.in_ = Wire( Bits4 )
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for s.in_ in range(4):
          s.out @= Bits4( 1 )
  DUT = SignalAsLoopIndexComp

class CaseRedefLoopIndexComp:
  class RedefLoopIndexComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range(4):
          for i in range(4):
            s.out @= Bits4( 1 )
  DUT = RedefLoopIndexComp

class CaseSignalAfterInComp:
  class SignalAfterInComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits2 )
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in s.in_:
          s.out @= Bits4( 1 )
  DUT = SignalAfterInComp

class CaseFuncCallAfterInComp:
  class FuncCallAfterInComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      def foo(): pass
      @update
      def upblk():
        for i in foo():
          s.out @= Bits4( 1 )
  DUT = FuncCallAfterInComp

class CaseNoArgsToRangeComp:
  class NoArgsToRangeComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range():
          s.out @= Bits4( 1 )
  DUT = NoArgsToRangeComp

class CaseTooManyArgsToRangeComp:
  class TooManyArgsToRangeComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        for i in range( 0, 4, 1, 1 ):
          s.out @= Bits4( 1 )
  DUT = TooManyArgsToRangeComp

class CaseInvalidIsComp:
  class InvalidIsComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) is Bits1( 1 )
  DUT = InvalidIsComp

class CaseInvalidIsNotComp:
  class InvalidIsNotComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) is not Bits1( 1 )
  DUT = InvalidIsNotComp

class CaseInvalidInComp:
  class InvalidInComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) in Bits1( 1 )
  DUT = InvalidInComp

class CaseInvalidNotInComp:
  class InvalidNotInComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) not in Bits1( 1 )
  DUT = InvalidNotInComp

class CaseInvalidDivComp:
  class InvalidDivComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 1 ) // Bits1( 1 )
  DUT = InvalidDivComp

class CaseMultiOpComparisonComp:
  class MultiOpComparisonComp( Component ):
    def construct( s ):
      s.out = OutPort( Bits4 )
      @update
      def upblk():
        s.out @= Bits1( 0 ) <= Bits2( 1 ) <= Bits2( 2 )
  DUT = MultiOpComparisonComp

class CaseInvalidBreakComp:
  class InvalidBreakComp( Component ):
    def construct( s ):
      @update
      def upblk():
        for i in range(42): break
  DUT = InvalidBreakComp

class CaseInvalidContinueComp:
  class InvalidContinueComp( Component ):
    def construct( s ):
      @update
      def upblk():
        for i in range(42): continue
  DUT = InvalidContinueComp

class CaseBitsAttributeComp:
  class BitsAttributeComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_.foo
  DUT = BitsAttributeComp

class CaseStructMissingAttributeComp:
  class StructMissingAttributeComp( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32Foo )
      s.out = OutPort( Bits1 )
      @update
      def upblk():
        s.out @= s.in_.bar
  DUT = StructMissingAttributeComp

class CaseInterfaceMissingAttributeComp:
  class InterfaceMissingAttributeComp( Component ):
    def construct( s ):
      s.in_ = Bits32OutIfc()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_.bar
  DUT = InterfaceMissingAttributeComp

class CaseSubCompMissingAttributeComp:
  class SubCompMissingAttributeComp( Component ):
    def construct( s ):
      s.comp = Bits32OutComp()
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.comp.bar
  DUT = SubCompMissingAttributeComp

class CaseCrossHierarchyAccessComp:
  class CrossHierarchyAccessComp( Component ):
    def construct( s ):
      s.comp = WrappedBits32OutComp()
      s.a_out = OutPort( Bits32 )
      @update
      def upblk():
        s.a_out @= s.comp.comp.out
  DUT = CrossHierarchyAccessComp

class CaseStarArgComp:
  class StarArgComp( Component ):
    def construct( s, *args ):
      pass
  DUT = StarArgComp

class CaseDoubleStarArgComp:
  class DoubleStarArgComp( Component ):
    def construct( s, **kwargs ):
      pass
  DUT = DoubleStarArgComp
