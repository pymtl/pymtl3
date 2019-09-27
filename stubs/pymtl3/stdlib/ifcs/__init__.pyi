from pymtl3.datatypes import Bits1
from pymtl3.dsl import Interface, InPort, OutPort

from typing import *

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
