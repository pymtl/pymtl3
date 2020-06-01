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

from .master_minion_ifcs import MasterIfcCL, MasterIfcRTL, MinionIfcCL, MinionIfcRTL
from .send_recv_ifcs import RecvCL2SendRTL, RecvIfcRTL, RecvRTL2SendCL, SendIfcRTL
from .XcelMsg import XcelMsgType, mk_xcel_msg

#-------------------------------------------------------------------------
# FL interfaces
#-------------------------------------------------------------------------
# We assume FL interfaces shouldn't take types by default and the CL one should ...

class XcelMasterIfcFL( Interface ):

  def construct( s ):
    s.read  = CallerIfcFL()
    s.write = CallerIfcFL()

  def __str__( s ):
    return f"r{s.read}|w{s.write}"

  def connect( s, other, parent ):
    if isinstance( other, XcelMinionIfcRTL ):
      m = XcelIfcFL2RTLAdapter( other.ReqType, other.RespType )

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
      m = XcelIfcFL2CLAdapter( other.ReqType, other.RespType )

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

  def construct( s, *, read=None, write=None ):
    s.read  = CalleeIfcFL( method=read )
    s.write = CalleeIfcFL( method=write )

  def __str__( s ):
    return f"r{s.read}|w{s.write}"

  def connect( s, other, parent ):
    if isinstance( other, XcelMasterIfcRTL ):
      m = XcelIfcRTL2FLAdapter( other.ReqType, other.RespType )

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
      m = XcelIfcCL2FLAdapter( other.ReqType, other.RespType )

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

  def line_trace( s ):
    return f"[r]{s.read}[w]{s.write}"

#-------------------------------------------------------------------------
# CL interfaces
#-------------------------------------------------------------------------

# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc. The CL-FL and FL-CL has been implemented in the FL ifc.

class XcelMasterIfcCL( MasterIfcCL ): pass

class XcelMinionIfcCL( MinionIfcCL ): pass

#-------------------------------------------------------------------------
# RTL interfaces
#-------------------------------------------------------------------------
# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc. The RTL-FL and FL-RTL has been implemented in the FL ifc.

class XcelMasterIfcRTL( MasterIfcRTL ): pass

class XcelMinionIfcRTL( MinionIfcRTL ): pass

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
    s.left  = XcelMinionIfcCL( ReqType, RespType, req=s.recv, req_rdy=s.recv_rdy )
    s.right = XcelMasterIfcFL()
    s.entry = None

    @update_once
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

        # Make line trace look better since s.right might get blocked
        assert s.left.resp.rdy()
        s.left.resp( resp )

    s.add_constraints(
      M( s.left.req ) > U( up_xcelifc_cl_fl_blk ), # add an edge
    )

class XcelIfcFL2CLAdapter( Component ):

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

    s.left  = XcelMinionIfcFL( read=s.read, write=s.write )
    s.right = XcelMasterIfcCL( ReqType, RespType, resp=s.recv, resp_rdy=s.recv_rdy )

    s.add_constraints(
      M( s.left.read  ) == M( s.right.req ),
      M( s.left.write ) == M( s.right.req ),
      M( s.left.read  ) > M( s.right.resp ),
      M( s.left.write ) > M( s.right.resp ),
    )

#-------------------------------------------------------------------------
# RTL/FL adapters
#-------------------------------------------------------------------------
# Yanghui: directly adapting FL/RTL is tricky. I first convert FL/CL
# then CL/RTL using the adapters we already have.

class XcelIfcRTL2FLAdapter( Component ):

  def construct( s, ReqType, RespType ):
    s.left  = XcelMinionIfcRTL( ReqType, RespType )
    s.right = XcelMasterIfcFL()

    s.req_rtl2cl = RecvRTL2SendCL( ReqType )
    s.resp_cl2rtl  = RecvCL2SendRTL( RespType )
    s.cl2fl = XcelIfcCL2FLAdapter( ReqType, RespType )

    s.left.req //= s.req_rtl2cl.recv
    s.req_rtl2cl.send //= s.cl2fl.left.req

    s.cl2fl.right //= s.right

    s.cl2fl.left.resp //= s.resp_cl2rtl.recv
    s.left.resp //= s.resp_cl2rtl.send

class XcelIfcFL2RTLAdapter( Component ):

  def construct( s, ReqType, RespType ):
    s.left  = XcelMinionIfcFL ()
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
