"""
==========================================================================
 xcel_ifcs.py
==========================================================================
Accelerator interface implementations at FL, CL, and RTL.

 Author: Yanghui Ou
   Date: June 3, 2019
"""
from greenlet import greenlet

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.rtl.queues import BypassQueueRTL, NormalQueueRTL

from .SendRecvIfc import RecvCL2SendRTL, RecvIfcRTL, RecvRTL2SendCL, SendIfcRTL
from .XcelMsg import XcelMsgType, mk_xcel_msg

#-------------------------------------------------------------------------
# FL interfaces
#-------------------------------------------------------------------------
# TODO: figure out how to do __str__ for FL interfaces.

class XcelMasterIfcFL( Interface ):

  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.read  = CallerPort()
    s.write = CallerPort()

  def connect( s, other, parent ):
    if isinstance( other, XcelMinionIfcRTL ):
      m = XcelIfcFL2RTLAdapter( s.ReqType, s.RespType )

      if hasattr( parent, "XcelIfcFL2RTL_count" ):
        count = parent.XcelIfcFL2RTL_count
        setattr( parent, "XcelIfcFL2RTL_" + str( count ), m )
      else:
        parent.XcelIfcFL2RTL_count = 0
        parent.XcelIfcFL2RTL_0 = m

      connect_pairs(
        s,       m.left,
        m.right, other,
      )
      parent.XcelIfcFL2RTL_count += 1
      return True

    elif isinstance( other, XcelMinionIfcCL ):
      m = XcelIfcFL2CLAdapter( s.ReqType, s.RespType )

      if hasattr( parent, "XcelIfcFL2CL_count" ):
        count = parent.XcelIfcFL2CL_count
        setattr( parent, "XcelIfcFL2CL_" + str( count ), m )
      else:
        parent.XcelIfcFL2CL_count = 0
        parent.XcelIfcFL2CL_0 = m

      connect_pairs(
        s,       m.left,
        m.right, other,
      )
      parent.XcelIfcFL2CL_count += 1
      return True

    return False

class XcelMinionIfcFL( Interface ):

  def construct( s, ReqType, RespType, read=None, write=None ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.read  = CalleePort( method=read )
    s.write = CalleePort( method=write )

  def connect( s, other, parent ):
    if isinstance( other, XcelMasterIfcRTL ):
      m = XcelIfcRTL2FLAdapter( s.ReqType, s.RespType )

      if hasattr( parent, "XcelIfcRTL2FL_count" ):
        count = parent.XcelIfcRTL2FL_count
        setattr( parent, "XcelIfcRTL2FL_" + str( count ), m )
      else:
        parent.XcelIfcRTL2FL_count = 0
        parent.XcelIfcRTL2FL_0 = m

      connect_pairs(
        other,   m.left,
        m.right, s,
      )
      parent.XcelIfcRTL2FL_count += 1
      return True

    elif isinstance( other, XcelMasterIfcCL ):
      m = XcelIfcCL2FLAdapter( s.ReqType, s.RespType )

      if hasattr( parent, "XcelIfcCL2FL_count" ):
        count = parent.XcelIfcCL2FL_count
        setattr( parent, "XcelIfcCL2FL_" + str( count ), m )
      else:
        parent.XcelIfcCL2FL_count = 0
        parent.XcelIfcCL2FL_0 = m

      connect_pairs(
        other,   m.left,
        m.right, s,
      )
      parent.XcelIfcCL2FL_count += 1
      return True

    return False

#-------------------------------------------------------------------------
# CL interfaces
#-------------------------------------------------------------------------

# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc. The CL-FL and FL-CL has been implemented in the FL ifc.

class XcelMasterIfcCL( Interface ):

  def construct( s, ReqType, RespType, resp=None, resp_rdy=None ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = NonBlockingCallerIfc( ReqType )
    s.resp = NonBlockingCalleeIfc( RespType, resp, resp_rdy )

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

class XcelMinionIfcCL( Interface ):

  def construct( s, ReqType, RespType, req=None, req_rdy=None ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = NonBlockingCalleeIfc( ReqType, req, req_rdy )
    s.resp = NonBlockingCallerIfc( RespType )

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

#-------------------------------------------------------------------------
# RTL interfaces
#-------------------------------------------------------------------------

# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc. The RTL-FL and FL-RTL has been implemented in the FL ifc.

class XcelMasterIfcRTL( Interface ):

  def construct( s, ReqType, RespType ):
    s.req  = SendIfcRTL( ReqType  )
    s.resp = RecvIfcRTL( RespType )

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

class XcelMinionIfcRTL( Interface ):
  def construct( s, ReqType, RespType ):
    s.req  = RecvIfcRTL( ReqType  )
    s.resp = SendIfcRTL( RespType )

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

#-------------------------------------------------------------------------
# CL/FL adapters
#-------------------------------------------------------------------------

class XcelIfcCL2FLAdapter( Component ):

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, ReqType, RespType ):
    s.left  = XcelMinionIfcCL( ReqType, RespType, s.recv, s.recv_rdy )
    s.right = XcelMasterIfcFL( ReqType, RespType )
    s.entry = None

    @s.update
    def up_xcelifc_cl_fl_blk():

      if s.entry is not None and s.left.resp.rdy():

        # Dequeue xcel request message
        req     = s.entry
        s.entry = None

        if req.type_ == XcelMsgType.READ:
          resp = RespType( req.type_, s.right.read(req.addr) )

        elif req.type_ == XcelMsgType.WRITE:
          s.right.write( req.addr, req.data )
          resp = RespType( req.type_, 0 )

        s.left.resp( resp )

    s.add_constraints(
      M( s.left.req ) > U( up_xcelifc_cl_fl_blk ), # add an edge
    )

class XcelIfcFL2CLAdapter( Component ):

  @blocking
  def read( s, addr ):

    # TODO: refactor this greenlet stuff into some utility API
    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.ReqType( XcelMsgType.READ, addr ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.entry.data
    s.entry = None
    return ret

  @blocking
  def write( s, addr, data ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.ReqType( XcelMsgType.WRITE, addr, data ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    s.entry = None

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, ReqType, RespType ):
    s.entry = None # store response

    s.ReqType  = ReqType

    s.left  = XcelMinionIfcFL( ReqType, RespType, s.read, s.write )
    s.right = XcelMasterIfcCL( ReqType, RespType, s.recv, s.recv_rdy )

    s.add_constraints(
      M( s.left.read  ) == M( s.right.req ),
      M( s.left.write ) == M( s.right.req ),
      M( s.left.read  ) > M( s.right.resp ),
      M( s.left.write ) > M( s.right.resp ),
    )

#-------------------------------------------------------------------------
# RTL/FL adapters
#-------------------------------------------------------------------------

class XcelIfcRTL2FLAdapter( Component ):

  def construct( s, ReqType, RespType ):
    s.left  = XcelMinionIfcRTL( ReqType, RespType )
    s.right = XcelMasterIfcFL( ReqType, RespType )

    s.req_q = NormalQueueRTL( ReqType, num_entries=1 )
    connect( s.left.req, s.req_q.enq )

    @s.update
    def up_xcelifc_rtl_fl_blk():

      if s.req_q.deq.rdy and s.left.resp.rdy:

        if s.req_q.deq.msg.type_ == XcelMsgType.READ:
          resp = RespType( s.req_q.deq.msg.type_,
                           s.right.read( s.req_q.deq.msg.addr ) )

        elif s.req_q.deq.msg.type_ == XcelMsgType.WRITE:
          s.right.write( s.req_q.deq.msg.addr, s.req_q.deq.msg.data )
          resp = RespType( s.req_q.deq.msg.type_, 0 )

        s.req_q.deq.en = b1(1)
        s.left.resp.en  = b1(1)
        s.left.resp.msg = resp

      else:
        s.req_q.deq.en = b1(0)
        s.left.resp.en  = b1(0)

# Yanghui: directly adapting FL to RTL is tricky. I first convert FL to CL
# then CL to RTL using the adapters we already have.
class XcelIfcFL2RTLAdapter( Component ):

  def construct( s, ReqType, RespType ):
    s.left  = XcelMinionIfcFL ( ReqType, RespType )
    s.right = XcelMasterIfcRTL( ReqType, RespType )

    s.fl2cl       = XcelIfcFL2CLAdapter( ReqType, RespType )
    s.req_cl2rtl  = RecvCL2SendRTL( ReqType )
    s.resp_rtl2cl = RecvRTL2SendCL( RespType)
    connect( s.left, s.fl2cl.left )
    connect_pairs(
      s.fl2cl.right.req, s.req_cl2rtl.recv,
      s.req_cl2rtl.send, s.right.req,
    )
    connect_pairs(
      s.fl2cl.right.resp, s.resp_rtl2cl.send,
      s.resp_rtl2cl.recv, s.right.resp,
    )
