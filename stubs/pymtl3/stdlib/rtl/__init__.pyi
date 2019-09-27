from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.datatypes import Bits1

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

  en : InPort [Bits1]
  in_: InPort [T_RegEnDataType]
  out: OutPort[T_RegEnDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

#-------------------------------------------------
# Arithmetics
#-------------------------------------------------

T_MuxDataType = TypeVar( "T_MuxDataType" )
T_MuxSelType  = TypeVar( "T_MuxSelType"  )

class Mux( Component, Generic[T_MuxDataType, T_MuxSelType] ):

  in_: List[InPort[T_MuxDataType]]
  sel: InPort [T_MuxSelType]
  out: OutPort[T_MuxDataType]

  def __init__( s, ninputs: int ) -> None: ...

  def construct( s, ninputs: int ) -> None: ...

T_LShifterDataType  = TypeVar( "T_LShifterDataType"  )
T_LShifterShamtType = TypeVar( "T_LShifterShamtType" )

class LShifter( Component, Generic[T_LShifterDataType, T_LShifterShamtType] ):

  in_  : InPort [T_LShifterDataType]
  shamt: InPort [T_LShifterShamtType]
  out  : OutPort[T_LShifterDataType]

  def __init__( s, shamt_nbits: int ) -> None: ...

  def construct( s, shamt_nbits: int ) -> None: ...

T_RShifterDataType  = TypeVar( "T_RShifterDataType"  )
T_RShifterShamtType = TypeVar( "T_RShifterShamtType" )

class RShifter( Component, Generic[T_RShifterDataType, T_RShifterShamtType] ):

  in_  : InPort [T_RShifterDataType]
  shamt: InPort [T_RShifterShamtType]
  out  : OutPort[T_RShifterDataType]

  def __init__( s, shamt_nbits: int ) -> None: ...

  def construct( s, shamt_nbits: int ) -> None: ...

T_SubtractorDataType = TypeVar( "T_SubtractorDataType" )

class Subtractor( Component, Generic[T_SubtractorDataType] ):

  in0: InPort [T_SubtractorDataType]
  in1: InPort [T_SubtractorDataType]
  out: OutPort[T_SubtractorDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...
