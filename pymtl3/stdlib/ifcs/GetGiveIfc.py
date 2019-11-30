"""
========================================================================
GetGiveIfc.py
========================================================================
RTL implementation of en/rdy micro-protocol.

Author: Yanghui Ou
  Date: Mar 19, 2019
"""
import greenlet

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.rtl import And

from .ifcs_utils import enrdy_to_str
from .SendRecvIfc import RecvIfcRTL

#-------------------------------------------------------------------------
# GetIfcRTL
#-------------------------------------------------------------------------

class GetIfcRTL( CallerIfcRTL ):
  def construct( s, Type ):
    super().construct( en=True, rdy=True, MsgType=None, RetType=Type )

#-------------------------------------------------------------------------
# GiveIfcRTL
#-------------------------------------------------------------------------

class GiveIfcRTL( CalleeIfcRTL ):
  def construct( s, Type ):
    super().construct( en=True, rdy=True, MsgType=None, RetType=Type )

  def connect( s, other, parent ):

    # We are doing GiveIfcRTL (s) -> [ AND ] -> RecvIfcRTL (other)
    # Basically we AND the rdy of both sides for enable
    if isinstance( other, RecvIfcRTL ):
      connect( s.ret, other.msg )

      m = And( Bits1 )

      if hasattr( parent, "deq_recv_ander_cnt" ):
        cnt = parent.give_recv_ander_cnt
        setattr( parent, "deq_recv_ander_" + str( cnt ), m )
      else:
        parent.give_recv_ander_cnt = 0
        parent.give_recv_ander_0   = m

      connect_pairs(
        m.in0, s.rdy,
        m.in1, other.rdy,
        m.out, s.en,
        m.out, other.en,
      )
      parent.give_recv_ander_cnt += 1
      return True

    return False


class GetIfcFL( CallerIfcFL ):

  def connect( s, other, parent ):

    # We are doing SendCL (other) -> [ RecvCL -> GiveIfcFL ] -> GetIfcFL (s)
    # SendCL is a caller interface
    if isinstance( other, CallerIfcCL ):
      m = RecvCL2GiveFL()

      if hasattr( parent, "RecvCL2GiveFL_count" ):
        count = parent.RecvCL2GiveFL_count
        setattr( parent, "RecvCL2GiveFL_" + str( count ), m )
      else:
        parent.RecvCL2GiveFL_count = 0
        parent.RecvCL2GiveFL_0 = m

      connect_pairs(
        other,  m.recv,
        m.give, s
      )
      parent.RecvCL2GiveFL_count += 1
      return True

    return False

class GiveIfcFL( CalleeIfcFL ):
  pass

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2GiveFL( Component ):

  @blocking
  def give( s ):
    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)
    ret = s.entry
    s.entry = None
    return ret

  @non_blocking( lambda s : s.entry is None )
  def recv( s, msg ):
    s.entry = msg

  def construct( s ):

    # Interface

    s.give = GiveIfcFL( s.give )

    s.entry = None

    s.add_constraints( M( s.recv ) == M( s.give ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.give )
