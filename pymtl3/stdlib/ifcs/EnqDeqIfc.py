"""
========================================================================
EnqDeqIfc.py
========================================================================
RTL implementation of deq and enq interface.

Author: Yanghui Ou
  Date: Mar 21, 2019
"""
from typing import TypeVar, Generic

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.rtl import And

from .GetGiveIfc import GiveIfcRTL
from .ifcs_utils import enrdy_to_str
from .SendRecvIfc import RecvIfcRTL

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------

T_EnqIfcDataType = TypeVar('T_EnqIfcDataType')

class EnqIfcRTL( RecvIfcRTL, Generic[T_EnqIfcDataType] ):

  def construct( s ):
    s.msg =  InPort[T_EnqIfcDataType]()
    s.en  =  InPort[Bits1]()
    s.rdy = OutPort[Bits1]()

    s.MsgType = T_EnqIfcDataType

#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------

T_DeqIfcDataType = TypeVar('T_DeqIfcDataType')

class DeqIfcRTL( GiveIfcRTL, Generic[T_DeqIfcDataType] ):

  def construct( s ):
    s.MsgType = T_DeqIfcDataType

    s.msg = OutPort[T_DeqIfcDataType]()
    s.en  = InPort [Bits1]()
    s.rdy = OutPort[Bits1]()

  # Interfaces are the same as GiveIfc. We just need to add custom connect

  def connect( s, other, parent ):

    # We are doing DeqIfcRTL (s) -> [ AND ] -> RecvIfcRTL (other)
    # Basically we AND the rdy of both sides for enable
    if isinstance( other, RecvIfcRTL ):
      connect( s.msg, other.msg )

      m = And( Bits1 )

      if hasattr( parent, "deq_recv_ander_cnt" ):
        cnt = parent.deq_recv_ander_cnt
        setattr( parent, "deq_recv_ander_" + str( cnt ), m )
      else:
        parent.deq_recv_ander_cnt = 0
        parent.deq_recv_ander_0   = m

      connect_pairs(
        m.in0, s.rdy,
        m.in1, other.rdy,
        m.out, s.en,
        m.out, other.en,
      )
      parent.deq_recv_ander_cnt += 1
      return True

    return False
