from pymtl3.dsl import Component, InPort, OutPort, RList
from pymtl3.datatypes import Bits1

from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL, EnqIfcRTL, DeqIfcRTL

from typing import *

#-------------------------------------------------
# Registers
#-------------------------------------------------

T_RegDataType = TypeVar( "T_RegDataType" )

class Reg( Component, Generic[T_RegDataType] ):

  in_: InPort [T_RegDataType]
  out: OutPort[T_RegDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_RegEnDataType = TypeVar( "T_RegEnDataType" )

class RegEn( Component, Generic[T_RegEnDataType] ):

  clk: InPort [Bits1]
  en : InPort [Bits1]
  in_: InPort [T_RegEnDataType]
  out: OutPort[T_RegEnDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_RegRstDataType = TypeVar( "T_RegRstDataType" )

class RegRst( Component, Generic[T_RegRstDataType] ):

  reset : InPort [Bits1]
  in_   : InPort [T_RegRstDataType]
  out   : OutPort[T_RegRstDataType]

  def __init__( s, reset_value : int = 0 ) -> None: ...

  def construct( s, reset_value : int = 0 ) -> None: ...

T_RegEnRstDataType = TypeVar( "T_RegEnRstDataType" )

class RegEnRst( Component, Generic[T_RegEnRstDataType] ):

  en    : InPort [Bits1]
  reset : InPort [Bits1]
  in_   : InPort [T_RegEnRstDataType]
  out   : OutPort[T_RegEnRstDataType]

  def __init__( s, reset_value : int = 0 ) -> None: ...

  def construct( s, reset_value : int = 0 ) -> None: ...

#-------------------------------------------------
# RegisterFile
#-------------------------------------------------

T_RFDpath = TypeVar('T_RFDpath')
T_RFAddr  = TypeVar('T_RFAddr')

class RegisterFile( Component, Generic[T_RFDpath, T_RFAddr] ):

  raddr     : RList[InPort[T_RFAddr], T_RFAddr]
  rdata     : RList[OutPort[T_RFDpath], T_RFDpath]
  waddr     : RList[InPort[T_RFAddr], T_RFAddr]
  wdata     : RList[InPort[T_RFDpath], T_RFDpath]
  wen       : RList[InPort[Bits1], Bits1]
  # regs      : RList[Wire[T_RFDpath], T_RFDpath]
  # next_regs : RList[Wire[T_RFDpath], T_RFDpath]

  def __init__( s, nregs : int = 32, rd_ports : int = 1, wr_ports : int = 1, const_zero : bool = False) -> None: ...

  def construct( s, nregs : int = 32, rd_ports : int = 1, wr_ports : int = 1, const_zero : bool = False) -> None: ...

#-------------------------------------------------
# Arithmetics
#-------------------------------------------------

T_MuxDataType = TypeVar( "T_MuxDataType" )
T_MuxSelType  = TypeVar( "T_MuxSelType"  )

class Mux( Component, Generic[T_MuxDataType, T_MuxSelType] ):

  in_: RList[InPort[T_MuxDataType], T_MuxDataType]
  sel: InPort [T_MuxSelType]
  out: OutPort[T_MuxDataType]

  @overload
  def __init__( s, ninputs: int ) -> None: ...

  @overload
  def __init__( s, Type: Any, SelType: Any, ninputs: int ) -> None: ...

  def construct( s, ninputs: int ) -> None: ...

T_LShifterDataType  = TypeVar( "T_LShifterDataType"  )
T_LShifterShamtType = TypeVar( "T_LShifterShamtType" )

class LShifter( Component, Generic[T_LShifterDataType, T_LShifterShamtType] ):

  in_  : InPort [T_LShifterDataType]
  shamt: InPort [T_LShifterShamtType]
  out  : OutPort[T_LShifterDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_RShifterDataType  = TypeVar( "T_RShifterDataType"  )
T_RShifterShamtType = TypeVar( "T_RShifterShamtType" )

class RShifter( Component, Generic[T_RShifterDataType, T_RShifterShamtType] ):

  in_  : InPort [T_RShifterDataType]
  shamt: InPort [T_RShifterShamtType]
  out  : OutPort[T_RShifterDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_SubtractorDataType = TypeVar( "T_SubtractorDataType" )

class Subtractor( Component, Generic[T_SubtractorDataType] ):

  in0: InPort [T_SubtractorDataType]
  in1: InPort [T_SubtractorDataType]
  out: OutPort[T_SubtractorDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_AdderDataType = TypeVar( "T_AdderDataType" )

class Adder( Component, Generic[T_AdderDataType] ):

  in0: InPort [T_AdderDataType]
  in1: InPort [T_AdderDataType]
  out: OutPort[T_AdderDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_IncrementerDataType = TypeVar( "T_IncrementerDataType" )

class Incrementer( Component, Generic[T_IncrementerDataType] ):

  in_: InPort [T_IncrementerDataType]
  out: OutPort[T_IncrementerDataType]

  def __init__( s, amount : int = 1 ) -> None: ...

  def construct( s, amount : int = 1 ) -> None: ...
