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
from pymtl3.dsl.errors import InvalidConnectionError
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.connects import connect_pairs

from .send_recv_ifcs import RecvIfcRTL

#-------------------------------------------------------------------------
# GetIfcRTL
#-------------------------------------------------------------------------

class GetIfcRTL( CallerIfcRTL ):
  def construct( s, Type ):
    super().construct( en=True, rdy=True, MsgType=None, RetType=Type )

#-------------------------------------------------------------------------
# GiveIfcRTL
#-------------------------------------------------------------------------

class And( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_and():
      s.out @= s.in0 & s.in1

class GiveIfcRTL( CalleeIfcRTL ):
  def construct( s, Type ):
    super().construct( en=True, rdy=True, MsgType=None, RetType=Type )

  def connect( s, other, parent ):
    # We are doing GiveIfcRTL (s) -> [ AND ] -> RecvIfcRTL (other)
    # Basically we AND the rdy of both sides for enable
    if isinstance( other, RecvIfcRTL ):
      connect( s.ret, other.msg )

      m = And( Bits1 )

      if hasattr( parent, "give_recv_ander_cnt" ):
        cnt = parent.give_recv_ander_cnt
        setattr( parent, "give_recv_ander_" + str( cnt ), m )
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

    elif isinstance( other, CalleeIfcCL ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between GiveIfcRTL"
            " and CalleeIfcCL.\n"
            "          - level {}: {} (class {})\n"
            "          - level {}: {} (class {})".format(
                s._dsl.level, repr( s ), type( s ), other._dsl.level,
                repr( other ), type( other ) ) )

      m = GetRTL2GiveCL( s.MsgType )

      if hasattr( parent, "GetRTL2GiveCL_count" ):
        count = parent.GetRTL2GiveCL_count
        setattr( parent, "GetRTL2GiveCL_" + str( count ), m )
      else:
        parent.GetRTL2GiveCL_count = 0
        parent.GetRTL2GiveCL_0 = m

      connect_pairs(
        s,      m.get,
        m.give, other,
      )
      parent.GetRTL2GiveCL_count += 1
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

    elif isinstance( other, RecvIfcRTL ):
      m = RecvRTL2GiveFL(other.MsgType)

      if hasattr( parent, "RecvRTL2GiveFL_count" ):
        count = parent.RecvRTL2GiveFL_count
        setattr( parent, "RecvRTL2GiveFL_" + str( count ), m )
      else:
        parent.RecvRTL2GiveFL_count = 0
        parent.RecvRTL2GiveFL_0 = m

      connect_pairs(
        other,  m.recv,
        m.give, s
      )
      parent.RecvRTL2GiveFL_count += 1
      return True

    return False

class GiveIfcFL( CalleeIfcFL ):
  pass

#-------------------------------------------------------------------------
# GetRTL2GiveCL
#-------------------------------------------------------------------------

class GetRTL2GiveCL( Component ):

  def construct( s, MsgType ):
    # Interface
    s.get = GetIfcRTL( MsgType )

    s.entry = None

    @update
    def up_get_rtl():
      if s.entry is None and s.get.rdy:
        s.get.en @= 1
      else:
        s.get.en @= 0

    @update
    def up_entry():
      if s.get.en:
        s.entry = clone_deepcopy( s.get.msg )

    s.add_constraints(
      U( up_get_rtl ) < M( s.give     ),
      U( up_get_rtl ) < M( s.give.rdy ),
      U( up_entry   ) < M( s.give     ),
      U( up_entry   ) < M( s.give.rdy ),
    )

  @non_blocking( lambda s : s.entry is not None )
  def give( s ):
    tmp = s.entry
    s.entry = None
    return tmp

  def line_trace( s ):
    return "{}(){}".format( s.get, s.give )

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

    s.entry = None

    s.add_constraints( M( s.recv ) > M( s.give ) ) # pipe behavior

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.give )

#-------------------------------------------------------------------------
# RecvRTL2GiveFL
#-------------------------------------------------------------------------

class RecvRTL2GiveFL( Component ):

  @blocking
  def give( s ):
    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)
    ret = s.entry
    s.entry = None
    return ret

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )

    s.entry = None

    @update_once
    def up_recv_rtl_rdy():
      s.recv.rdy @= s.entry is not None

    @update_once
    def up_recv_cl():
      s.entry = None
      if s.recv.en:
        assert s.entry is None
        s.entry = deepcopy( s.recv.msg )

    s.add_constraints( U( up_recv_cl ) < M(s.give) ) # bypass

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )
