from typing import TypeVar, Generic
from pymtl3.dsl import Component
from pymtl3.stdlib.ifcs import EnqIfcRTL, DeqIfcRTL, SendIfcRTL, RecvIfcRTL

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
