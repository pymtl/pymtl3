"""
========================================================================
EnqDeqIfc.py
========================================================================
RTL implementation of deq and enq interface.

Author: Yanghui Ou
  Date: Mar 21, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.rtl import And

from .GetGiveIfc import GiveIfcRTL
from .ifcs_utils import enrdy_to_str
from .SendRecvIfc import RecvIfcRTL

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------

class EnqIfcRTL( RecvIfcRTL ):
  pass

#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------

class DeqIfcRTL( GiveIfcRTL ):

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
