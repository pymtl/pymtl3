from pymtl3 import *

from typing import *

# N-input Mux

T_Mux = TypeVar("T_Mux", bound=HWDataType)
class Mux( Component, Generic[T_Mux] ):

  def construct( s, Width: Type[T_Mux], ninputs: int ) -> None:
    assert ninputs > 0
    s.in_ = [ InPort( Width ) for _ in range(ninputs) ]
    s.out = OutPort( Width )
    s.sel = InPort( max(1, clog2(ninputs)) ) # allow 1-input

    @update
    def up_mux():
      s.out @= s.in_[ s.sel ]

# Rshifter

T_RShift      = TypeVar("T_RShift", bound=Bits)
T_RShiftShamt = TypeVar("T_RShiftShamt", bound=Bits)
class RightLogicalShifter( Component, Generic[T_RShift, T_RShiftShamt] ):

  def construct( s, Width: Type[T_RShift], ShamtWidth: Type[T_RShiftShamt] ) -> None:
    s.in_   = InPort( Width )
    s.shamt = InPort( ShamtWidth )
    s.out   = OutPort( Width )

    @update
    def up_rshifter():
      s.out @= s.in_ >> s.shamt

# Lshifter

T_LShift      = TypeVar("T_LShift", bound=Bits)
T_LShiftShamt = TypeVar("T_LShiftShamt", bound=Bits)
class LeftLogicalShifter( Component, Generic[T_LShift, T_LShiftShamt] ):

  def construct( s, Width: Type[T_LShift], ShamtWidth: Type[T_LShiftShamt] ) -> None:
    s.in_   = InPort( Width )
    s.shamt = InPort( ShamtWidth )
    s.out   = OutPort( Width )
    # assert shamt_nbits == Width.nbits

    @update
    def up_lshifter():
      s.out @= s.in_ << s.shamt

# Incrementer

T_Incr = TypeVar("T_Incr", bound=Bits)
class Incrementer( Component, Generic[T_Incr] ):

  def construct( s, Width: Type[T_Incr], amount : int = 1 ) -> None:
    s.in_ = InPort( Width )
    s.out = OutPort( Width )

    @update
    def up_incrementer():
      s.out @= s.in_ + amount

# Adder

T_Adder = TypeVar("T_Adder", bound=Bits)
class Adder( Component, Generic[T_Adder] ):

  def construct( s, Width: Type[T_Adder] ) -> None:
    s.in0 = InPort( Width )
    s.in1 = InPort( Width )
    s.out = OutPort( Width )

    @update
    def up_adder():
      s.out @= s.in0 + s.in1

# And

T_And = TypeVar("T_And", bound=Bits)
class And( Component, Generic[T_And] ):

  def construct( s, Width: Type[T_And] ) -> None:
    s.in0 = InPort( Width )
    s.in1 = InPort( Width )
    s.out = OutPort( Width )

    @update
    def up_and():
      s.out @= s.in0 & s.in1

# Subtractor

T_Sub = TypeVar("T_Sub", bound=Bits)
class Subtractor( Component, Generic[T_Sub] ):

  def construct( s, Width: Type[T_Sub] ) -> None:
    s.in0 = InPort( Width )
    s.in1 = InPort( Width )
    s.out = OutPort( Width )

    @update
    def up_subtractor():
      s.out @= s.in0 - s.in1

# ZeroComparator

T_ZCmp = TypeVar("T_ZCmp", bound=Bits)
class ZeroComparator( Component, Generic[T_ZCmp] ):

  def construct( s, Width: Type[T_ZCmp] ) -> None:
    s.in_ = InPort( Width )
    s.out = OutPort()

    @update
    def up_zerocomp():
      s.out @= s.in_ == 0

# LeftThanComparator

T_LTCmp = TypeVar("T_LTCmp", bound=Bits)
class LTComparator( Component, Generic[T_LTCmp] ):

  def construct( s, Width: Type[T_LTCmp] ) -> None:
    s.in0 = InPort( Width )
    s.in1 = InPort( Width )
    s.out = OutPort()

    @update
    def up_ltcomp():
      s.out @= s.in0 < s.in1

# LeftThanOrEqualToComparator

T_LECmp = TypeVar("T_LECmp", bound=Bits)
class LEComparator( Component, Generic[T_LECmp] ):

  def construct( s, Width: Type[T_LECmp] ) -> None:
    s.in0 = InPort( Width )
    s.in1 = InPort( Width )
    s.out = OutPort()

    @update
    def up_lecomp():
      s.out @= s.in0 <= s.in1
