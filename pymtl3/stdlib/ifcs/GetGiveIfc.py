"""
========================================================================
GetGiveIfc.py
========================================================================
RTL implementation of en/rdy micro-protocol.

Author: Yanghui Ou
  Date: Mar 19, 2019
"""
from __future__ import absolute_import, division, print_function

from copy import deepcopy
import greenlet

from pymtl3 import *
from pymtl3.dsl.errors import InvalidConnectionError
from pymtl3.stdlib.rtl import And

from .ifcs_utils import MethodSpec, enrdy_to_str
from .SendRecvIfc import RecvIfcRTL

#-------------------------------------------------------------------------
# GetIfcRTL
#-------------------------------------------------------------------------

class GetIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = InPort ( Type )
    s.en  = OutPort( int if Type is int else Bits1 )
    s.rdy = InPort ( int if Type is int else Bits1 )

    s.MsgType = Type

  def line_trace( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( "{}".format( s.MsgType() ) )
      trace_len = s.trace_len

    return enrdy_to_str( s.msg, s.en, s.rdy, trace_len )

  def __str__( s ):
    return s.line_trace()

#-------------------------------------------------------------------------
# GiveIfcRTL
#-------------------------------------------------------------------------

class GiveIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.en  = InPort ( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

    s.MsgType = Type
    s._mspec = MethodSpec()
    s._mspec.ret = { 'msg' : Type }

  def line_trace( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( "{}".format( s.MsgType() ) )
      trace_len = s.trace_len

    return enrdy_to_str( s.msg, s.en, s.rdy, trace_len )

  def __str__( s ):
    return s.line_trace()

  def connect( s, other, parent ):

    # We are doing DeqIfcRTL (s) -> [ AND ] -> RecvIfcRTL (other)
    # Basically we AND the rdy of both sides for enable
    if isinstance( other, RecvIfcRTL ):
      parent.connect( s.msg, other.msg )

      m = And( Bits1 )

      if hasattr( parent, "deq_recv_ander_cnt" ):
        cnt = parent.deq_recv_ander_cnt
        setattr( parent, "deq_recv_ander_" + str( cnt ), m )
      else:
        parent.deq_recv_ander_cnt = 0
        parent.deq_recv_ander_0   = m

      parent.connect_pairs(
        m.in0, s.rdy,
        m.in1, other.rdy,
        m.out, s.en,
        m.out, other.en,
      )
      parent.deq_recv_ander_cnt += 1
      return True

    elif isinstance( other, NonBlockingCalleeIfc ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between RecvIfcRTL"
            " and NonBlockingCalleeIfc.\n"
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

      parent.connect_pairs(
        s,      m.get,
        m.give, other,
      )
      parent.GetRTL2GiveCL_count += 1
      return True

    return False

class GetIfcFL( Interface ):

  def construct( s ):
    s.method = CallerPort()

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def line_trace( s ):
    return ''

  def __str__( s ):
    return s.line_trace()

  def connect( s, other, parent ):

    # We are doing SendCL (other) -> [ RecvCL -> GiveIfcFL ] -> GetIfcFL (s)
    # SendCL is a caller interface
    if isinstance( other, NonBlockingCallerIfc ):
      m = RecvCL2GiveFL()

      if hasattr( parent, "RecvCL2GiveFL_count" ):
        count = parent.RecvCL2GiveFL_count
        setattr( parent, "RecvCL2GiveFL_" + str( count ), m )
      else:
        parent.RecvCL2GiveFL_count = 0
        parent.RecvCL2GiveFL_0 = m

      parent.connect_pairs(
        other,  m.recv,
        m.give, s
      )
      parent.RecvCL2GiveFL_count += 1
      return True

    return False

#-------------------------------------------------------------------------
# GetRTL2GiveCL
#-------------------------------------------------------------------------

class GetRTL2GiveCL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.get  = GetIfcRTL( MsgType )

    s.entry = None

    @s.update
    def up_get_rtl():
      if s.entry is None and s.get.rdy:
        s.get.en = Bits1(1)
        s.entry  = deepcopy( s.get.msg )
      else:
        s.get.en = Bits1(0)

    s.add_constraints(
      U( up_get_rtl )   < M( s.give ),
      U( up_get_rtl )   < M( s.give.rdy ),
    )

  @non_blocking( lambda s : s.entry is not None )
  def give( s, msg ):
    tmp = deepcopy( s.entry )
    s.entry = None
    return tmp

  def line_trace( s ):
    return "{}(){}".format( s.get, s.give )

class GiveIfcFL( Interface ):

  def construct( s, method ):
    s.method = CalleePort( method=method )

  def line_trace( s ):
    return ''

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def __str__( s ):
    return s.line_trace()

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
