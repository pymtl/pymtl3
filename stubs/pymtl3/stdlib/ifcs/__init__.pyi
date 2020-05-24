from pymtl3.datatypes import Bits1
from pymtl3.dsl import Interface, InPort, OutPort

from typing import Generic, TypeVar

#-------------------------------------------------
# ValRdyIfc
#-------------------------------------------------

T_InValRdyIfc = TypeVar( "T_InValRdyIfc" )

class InValRdyIfc( Interface, Generic[T_InValRdyIfc] ):

  msg: InPort [T_InValRdyIfc]
  val: InPort [Bits1]
  rdy: OutPort[Bits1]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_OutValRdyIfc = TypeVar( "T_OutValRdyIfc" )

class OutValRdyIfc( Interface, Generic[T_OutValRdyIfc] ):

  msg: OutPort[T_OutValRdyIfc]
  val: OutPort[Bits1]
  rdy: InPort [Bits1]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

#-------------------------------------------------
# Send/Recv Ifc
#-------------------------------------------------

T_RecvIfcDataType = TypeVar('T_RecvIfcDataType')

class RecvIfcRTL( Interface, Generic[T_RecvIfcDataType] ):

  msg: InPort[T_RecvIfcDataType]
  en : InPort[Bits1]
  rdy: OutPort[Bits1]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

T_SendIfcDataType = TypeVar('T_SendIfcDataType')

class SendIfcRTL( Interface, Generic[T_SendIfcDataType] ):

  msg: OutPort[T_SendIfcDataType]
  en : OutPort[Bits1]
  rdy: InPort[Bits1]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...

#-------------------------------------------------
# Xcel Ifc
#-------------------------------------------------

T_XcelMasterIfcReqType  = TypeVar('T_XcelMasterIfcReqType')
T_XcelMasterIfcRespType = TypeVar('T_XcelMasterIfcRespType')

class XcelMasterIfcRTL( Interface, Generic[T_XcelMasterIfcReqType, T_XcelMasterIfcRespType] ):

  req:  SendIfcRTL[T_XcelMasterIfcReqType]
  resp: RecvIfcRTL[T_XcelMasterIfcRespType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...
