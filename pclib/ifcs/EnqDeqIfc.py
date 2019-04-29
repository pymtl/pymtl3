from __future__ import absolute_import
#=========================================================================
# EnqDeqIfc.py
#=========================================================================
# RTL implementation of deq and enq interface.
#
# Author: Yanghui Ou
#   Date: Mar 21, 2019

from builtins import str
from pymtl import *
from .ifcs_utils import enrdy_to_str
from .GuardedIfc import *
from .send_recv_ifc_adapters import RecvCL2SendRTL, RecvRTL2SendCL

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------

class EnqIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = InPort ( Type )
    s.en  = InPort ( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

    s.MsgType = Type

  def connect( s, other, parent ):
    if isinstance( other, GuardedCallerIfc ):

      m = RecvCL2SendRTL( s.MsgType )
      
      if hasattr( parent, "enq_adapter_cnt" ):
        cnt = parent.enq_adapter_cnt
        setattr( parent, "enq_adapter_" + str( cnt ), m )
        parent.connect_pairs(
          other,  m.recv,
          m.send, s
        )
        parent.enq_adapter_cnt += 1
        return True

      else:
        parent.enq_adapter_0 = m
        parent.connect_pairs(
          other,      m.recv,
          m.send.msg, s.msg,
          m.send.en,  s.en,
          m.send.rdy, s.rdy
        )
        parent.enq_adapter_cnt = 1
        return True

    return False

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy )

  def __str__( s ):
    return s.line_trace()

#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------

class DeqIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.en  = InPort ( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

    s.MsgType = Type

  def line_trace( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy )

  def __str__( s ):
    return s.line_trace()
