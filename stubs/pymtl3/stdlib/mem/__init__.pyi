from pymtl3.dsl import Interface
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL

from typing import Generic, TypeVar

#-------------------------------------------------
# Mem Ifc
#-------------------------------------------------

T_MemMasterIfcReqType  = TypeVar('T_MemMasterIfcReqType')
T_MemMasterIfcRespType = TypeVar('T_MemMasterIfcRespType')

class MemMasterIfcRTL( Interface, Generic[T_MemMasterIfcReqType, T_MemMasterIfcRespType] ):

  req:  SendIfcRTL[T_MemMasterIfcReqType]
  resp: RecvIfcRTL[T_MemMasterIfcRespType]

  def __init__( s ) -> None: ...

  def construct( s ) -> None: ...
