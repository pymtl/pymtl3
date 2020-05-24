from typing import Generic, TypeVar
from pymtl3.datatypes import Bits1
from pymtl3.dsl import Interface, InPort, OutPort, Component
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

#-------------------------------------------------
# Enq/Deq Ifc
#-------------------------------------------------

T_EnqIfcDataType = TypeVar('T_EnqIfcDataType')

class EnqIfcRTL( Interface, Generic[T_EnqIfcDataType] ):

  msg: InPort[T_EnqIfcDataType]
  en : InPort[Bits1]
  rdy: OutPort[Bits1]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_DeqIfcDataType = TypeVar('T_DeqIfcDataType')

class DeqIfcRTL( Interface, Generic[T_DeqIfcDataType] ):

  ret: OutPort[T_DeqIfcDataType]
  en : InPort[Bits1]
  rdy: OutPort[Bits1]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

#-------------------------------------------------
# Queues
#-------------------------------------------------

T_BpsQRTLDataType = TypeVar( "T_BpsQRTLDataType" )

class BypassQueueRTL( Component, Generic[T_BpsQRTLDataType] ):

  enq : EnqIfcRTL[T_BpsQRTLDataType]
  deq : DeqIfcRTL[T_BpsQRTLDataType]

  def __init__( s, n : int ) -> None: ...

  def construct( s, n : int ) -> None: ...

T_BpsQ1RTLDataType = TypeVar( "T_BpsQ1RTLDataType" )

class BypassQueue1RTL( Component, Generic[T_BpsQ1RTLDataType] ):

  enq : RecvIfcRTL[T_BpsQ1RTLDataType]
  deq : SendIfcRTL[T_BpsQ1RTLDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_BpsQ2RTLDataType = TypeVar( "T_BpsQ2RTLDataType" )

class BypassQueue2RTL( Component, Generic[T_BpsQ2RTLDataType] ):

  enq : RecvIfcRTL[T_BpsQ2RTLDataType]
  deq : SendIfcRTL[T_BpsQ2RTLDataType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...
