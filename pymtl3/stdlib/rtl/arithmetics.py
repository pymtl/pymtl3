
from typing import Generic, TypeVar
from pymtl3 import *

# N-input Mux

T_MuxDataType = TypeVar("T_MuxDataType")
T_MuxSelType  = TypeVar("T_MuxSelType")

class Mux( Component, Generic[T_MuxDataType, T_MuxSelType] ):

  def construct( s, ninputs ):
    s.in_ = [ InPort[T_MuxDataType]() for _ in range(ninputs) ]
    # s.sel = InPort( int if Type is int else mk_bits( clog2(ninputs) ) )
    s.sel = InPort[T_MuxSelType]()
    s.out = OutPort[T_MuxDataType]()

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

# Rshifter

T_RShifterDataType  = TypeVar("T_RShifterDataType")
T_RShifterShamtType = TypeVar("T_RShifterShamtType")

class RShifter( Component, Generic[T_RShifterDataType, T_RShifterShamtType] ):

  def construct( s ):
    s.in_   = InPort[T_RShifterDataType]()
    # s.shamt = InPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.shamt = InPort[T_RShifterShamtType]()
    s.out   = OutPort[T_RShifterDataType]()

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

# Lshifter

T_LShifterDataType  = TypeVar("T_LShifterDataType")
T_LShifterShamtType = TypeVar("T_LShifterShamtType")

class LShifter( Component, Generic[T_LShifterDataType, T_LShifterShamtType] ):

  def construct( s ):
    s.in_   = InPort[T_LShifterDataType]()
    # s.shamt = InPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.shamt = InPort[T_LShifterShamtType]()
    s.out   = OutPort[T_LShifterDataType]()

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

# Incrementer

class Incrementer( Component ):

  def construct( s, Type, amount=1 ):
    s.in_ = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_incrementer():
      s.out = s.in_ + Type(amount)

# Adder

class Adder( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_adder():
      s.out = s.in0 + s.in1

# And

class And( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_and():
      s.out = s.in0 & s.in1

# Subtractor

T_SubtractorDataType = TypeVar("T_SubtractorDataType")

class Subtractor( Component, Generic[T_SubtractorDataType] ):

  def construct( s ):
    s.in0 = InPort[T_SubtractorDataType]()
    s.in1 = InPort[T_SubtractorDataType]()
    s.out = OutPort[T_SubtractorDataType]()

    @s.update
    def up_subtractor():
      s.out = s.in0 - s.in1

# ZeroComparator

class ZeroComp( Component ):

  def construct( s, Type ):
    s.in_ = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_zerocomp():
      # s.out = Bits1( s.in_ == Type(0) )
      s.out = s.in_ == Type(0)

# LeftThanComparator

class LTComp( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_ltcomp():
      s.out = Bits1(s.in0 < s.in1)

# LeftThanOrEqualToComparator

class LEComp( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_lecomp():
      s.out = Bits1(s.in0 <= s.in1)
