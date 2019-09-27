from pymtl3.datatypes import Bits

from typing import *

#-------------------------------------------------------------------------
# Interface
#-------------------------------------------------------------------------

class Interface: ...

#-------------------------------------------------------------------------
# Component
#-------------------------------------------------------------------------

class Component:

  def update( s, func ) -> None: ...
  def update_on_edge( s, func ) -> None: ...

#-------------------------------------------------------------------------
# InPort
#-------------------------------------------------------------------------

T_InPortDataType = TypeVar("T_InPortDataType")

class InPort(Generic[T_InPortDataType]): ...

#-------------------------------------------------------------------------
# OutPort
#-------------------------------------------------------------------------

T_OutPortDataType = TypeVar("T_OutPortDataType")

class OutPort(Generic[T_OutPortDataType]): ...

#-------------------------------------------------------------------------
# Wire
#-------------------------------------------------------------------------

T_WireDataType = TypeVar("T_WireDataType")

class Wire(Generic[T_WireDataType]): ...

#-------------------------------------------------------------------------
# Const
#-------------------------------------------------------------------------

T_ConstDataType = TypeVar("T_ConstDataType")

class Const(Generic[T_ConstDataType]):

  def __init__( s, value: int = 0 ) -> None:
    ...

#-------------------------------------------------------------------------
# connect
#-------------------------------------------------------------------------

T_connect = TypeVar( "T_connect" )

def connect( u: Bits[T_connect], v: Bits[T_connect] ) -> None: ...
