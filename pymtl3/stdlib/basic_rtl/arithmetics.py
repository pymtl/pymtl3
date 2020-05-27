from typing import Generic, TypeVar
from pymtl3 import *
from pymtl3.dsl import Const

# N-input Mux

T_MuxDataType = TypeVar("T_MuxDataType")
T_MuxSelType  = TypeVar("T_MuxSelType")

class Mux( Component, Generic[T_MuxDataType, T_MuxSelType] ):

  #----------------------------------------------
  # Patch mypyc
  #----------------------------------------------

  # def __init__( s, Type, SelType, ninputs ):
  #   s.in_ = [ InPort[T_MuxDataType](Type) for _ in range(ninputs) ]
  #   s.sel = InPort[T_MuxSelType](SelType)
  #   s.out = OutPort[T_MuxDataType](Type)

  # def mux_upblk( s ):
  #   s.out = s.in_[s.sel]

  # def c_tick( s ):
  #   s.mux_upblk()

  #----------------------------------------------
  # End mypyc patch
  #----------------------------------------------

  def construct( s, ninputs ):
    s.in_ = [ InPort[T_MuxDataType]() for _ in range(ninputs) ]
    s.sel = InPort[T_MuxSelType]()
    s.out = OutPort[T_MuxDataType]()

    @update
    def up_mux():
      s.out @= s.in_[ s.sel ]

# Rshifter

T_RShifterDataType  = TypeVar("T_RShifterDataType")
T_RShifterShamtType = TypeVar("T_RShifterShamtType")

class RShifter( Component, Generic[T_RShifterDataType, T_RShifterShamtType] ):

  #----------------------------------------------
  # Patch mypyc
  #----------------------------------------------

  # def __init__( s, Type, ShamtType ):
  #   s.in_ = InPort[T_RShifterDataType](Type)
  #   s.shamt = InPort[T_RShifterShamtType](ShamtType)
  #   s.out = OutPort[T_RShifterDataType](Type)

  # def rshift_upblk( s ):
  #   s.out = s.in_ >> s.shamt

  # def c_tick( s ):
  #   s.rshift_upblk()

  #----------------------------------------------
  # End mypyc patch
  #----------------------------------------------

  def construct( s ):
    s.in_   = InPort[T_RShifterDataType]()
    # s.shamt = InPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.shamt = InPort[T_RShifterShamtType]()
    s.out   = OutPort[T_RShifterDataType]()

    @update
    def up_rshifter():
      s.out @= s.in_ >> s.shamt

# Lshifter

T_LShifterDataType  = TypeVar("T_LShifterDataType")
T_LShifterShamtType = TypeVar("T_LShifterShamtType")

class LShifter( Component, Generic[T_LShifterDataType, T_LShifterShamtType] ):

  #----------------------------------------------
  # Patch mypyc
  #----------------------------------------------

  # def __init__( s, Type, ShamtType ):
  #   s.in_ = InPort[T_LShifterDataType](Type)
  #   s.shamt = InPort[T_LShifterShamtType](ShamtType)
  #   s.out = OutPort[T_LShifterDataType](Type)

  # def rshift_upblk( s ):
  #   s.out = s.in_ << s.shamt

  # def c_tick( s ):
  #   s.lshift_upblk()

  #----------------------------------------------
  # End mypyc patch
  #----------------------------------------------

  def construct( s ):
    s.in_   = InPort[T_LShifterDataType]()
    # s.shamt = InPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.shamt = InPort[T_LShifterShamtType]()
    s.out   = OutPort[T_LShifterDataType]()

    @update
    def up_lshifter():
      s.out @= s.in_ << s.shamt

# Incrementer

T_IncrementerDataType = TypeVar("T_IncrementerDataType")

class Incrementer( Component, Generic[T_IncrementerDataType] ):

  def construct( s, amount=1 ):
    s.in_ = InPort [T_IncrementerDataType]()
    s.out = OutPort[T_IncrementerDataType]()

    Incr = Const[T_IncrementerDataType](amount)

    @update
    def up_incrementer():
      s.out @= s.in_ + Incr

# Adder

T_AdderDataType = TypeVar("T_AdderDataType")

class Adder( Component, Generic[T_AdderDataType] ):

  def construct( s ):
    s.in0 = InPort [T_AdderDataType]()
    s.in1 = InPort [T_AdderDataType]()
    s.out = OutPort[T_AdderDataType]()

    @update
    def up_adder():
      s.out @= s.in0 + s.in1

# And

class And( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_and():
      s.out @= s.in0 & s.in1

# Subtractor

T_SubtractorDataType = TypeVar("T_SubtractorDataType")

class Subtractor( Component, Generic[T_SubtractorDataType] ):

  #----------------------------------------------
  # Patch mypyc
  #----------------------------------------------

  # def __init__( s, Type ):
  #   s.in0 = InPort[T_SubtractorDataType](Type)
  #   s.in1 = InPort[T_SubtractorDataType](Type)
  #   s.out = OutPort[T_SubtractorDataType](Type)

  # def subtract_upblk( s ):
  #   s.out = s.in0 - s.in1

  # def c_tick( s ):
  #   s.subtract_upblk()

  #----------------------------------------------
  # End mypyc patch
  #----------------------------------------------

  def construct( s ):
    s.in0 = InPort[T_SubtractorDataType]()
    s.in1 = InPort[T_SubtractorDataType]()
    s.out = OutPort[T_SubtractorDataType]()

    @update
    def up_subtractor():
      s.out @= s.in0 - s.in1

# ZeroComparator

class ZeroComparator( Component ):

  def construct( s, Type ):
    s.in_ = InPort( Type )
    s.out = OutPort()

    @update
    def up_zerocomp():
      s.out @= s.in_ == 0

# LeftThanComparator

class LTComparator( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort()

    @update
    def up_ltcomp():
      s.out @= s.in0 < s.in1

# LeftThanOrEqualToComparator

class LEComparator( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort()

    @update
    def up_lecomp():
      s.out @= s.in0 <= s.in1
