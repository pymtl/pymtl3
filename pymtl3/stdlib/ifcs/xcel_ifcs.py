"""
==========================================================================
 xcel_ifcs.py
==========================================================================
Accelerator interface implementations at FL, CL, and RTL.

 Author: Yanghui Ou
   Date: June 3, 2019
"""
from __future__ import absolute_import, division, print_function

from greenlet import greenlet

from pymtl3 import *

from .SendRecvIfc import RecvIfcRTL, SendIfcRTL
from .XcelMsg import XcelMsgType, mk_xcel_msg

#=========================================================================
# FL interfaces
#=========================================================================

class XcelMasterIfcFL( Interface ):
  def construct( s ):
    s.read  = CallerPort()
    s.write = CallerPort()
  # TODO: implement __str__.

class XcelMinionIfcFL( Interface ):
  def construct( s, read, write ):
    s.read  = CalleePort( method=read )
    s.write = CalleePort( method=write )

#=========================================================================
# CL interfaces
#=========================================================================

class XcelMasterIfcCL( Interface ):
  def construct( s, req_class, resp_class, resp=None, resp_rdy=None ):
    s.req_class  = req_class
    s.resp_class = resp_class
    s.req  = NonBlockingCallerIfc( req_class )
    s.resp = NonBlockingCalleeIfc( resp_class, resp, resp_rdy )

  def line_trace( s ):
    return "{},{}".format( s.req, s.resp )

  def connect( s, other, parent ):
    if isinstance( other, XcelMinionIfcFL ):
      m = XcelIfcCL2FLAdapter( s.req_class, s.resp_class )

      if hasattr( parent, "XcelIfcCL2FL_count" ):
        count = parent.XcelIfcCL2FL_count
        setattr( parent, "XcelIfcCL2FL_" + str( count ), m )
      else:
        parent.XcelIfcCL2FL_count = 0
        parent.XcelIfcCL2FL_0 = m

      parent.connect_pairs(
        s,       m.left,
        m.right, other,
      )
      parent.XcelIfcCL2FL_count += 1
      return True
    elif isinstance( other, XcelMinionIfcCL ):
      assert s.req_class is other.req_class and s.resp_class is other.resp_class
      return False # use the default connect-by-name method

    return False

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

class XcelMinionIfcCL( Interface ):
  def construct( s, req_class, resp_class, req=None, req_rdy=None ):
    s.req_class  = req_class
    s.resp_class = resp_class
    s.req  = NonBlockingCalleeIfc( req_class, req, req_rdy )
    s.resp = NonBlockingCallerIfc( resp_class )

  def line_trace( s ):
    return "{},{}".format( s.req, s.resp )
  
  # TODO: implement CL-RTL connection
  def connect( s, other, parent ):
    if isinstance( other, XcelMasterIfcFL ):
      m = XcelIfcFL2CLAdapter( s.req_class, s.resp_class )

      if hasattr( parent, "XcelIfcFL2CL_count" ):
        count = parent.XcelIfcFL2CL_count
        setattr( parent, "XcelIfcFL2CL_" + str( count ), m )
      else:
        parent.XcelIfcFL2CL_count = 0
        parent.XcelIfcFL2CL_0 = m

      parent.connect_pairs(
        other,   m.left,
        m.right, s,
      )
      parent.XcelIfcFL2CL_count += 1
      return True

    elif isinstance( other, XcelMinionIfcCL ):
      assert s.req_class is other.req_class and s.resp_class is other.resp_class
      return False # use the default connect-by-name method

    return False

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

#=========================================================================
# RTL interfaces
#=========================================================================

class XcelMasterIfcRTL( Interface ):
  def construct( s, req_class, resp_class ):
    s.req  = SendIfcRTL( req_class  )
    s.resp = RecvIfcRTL( resp_class )

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

class XcelMinionIfcRTL( Interface ):
  def construct( s, req_class, resp_class ):
    s.req  = RecvIfcRTL( req_class  )
    s.resp = SendIfcRTL( resp_class )

  def __str__( s ):
    return "{},{}".format( s.req, s.resp )

#=========================================================================
# CL/FL adapters
#=========================================================================

class XcelIfcCL2FLAdapter( Component ):

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, req_class, resp_class ):
    s.left  = XcelMinionIfcCL( req_class, resp_class, s.recv, s.recv_rdy )
    s.right = XcelMasterIfcFL()
    s.entry = None

    @s.update
    def up_xcelifc_cl_fl_blk():

      if s.entry is not None and s.left.resp.rdy():

        # Dequeue xcel request message

        req     = s.entry
        s.entry = None

        if req.type_ == XcelMsgType.READ:
          resp = resp_class( req.type_, s.right.read( req.addr ) )

        elif req.type_ == XcelMsgType.WRITE:
          s.right.write( req.addr, req.data )
          resp = resp_class( req.type_, 0 )

        s.left.resp( resp )

    s.add_constraints(
      M( s.left.req ) < U( up_xcelifc_cl_fl_blk ), # bypass behavior
    )

class XcelIfcFL2CLAdapter( Component ):

  @blocking
  def read( s, addr ):

    # TODO: refactor this greenlet stuff into some utility API
    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.req_class( XcelMsgType.READ, addr ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.entry.data
    s.entry = None
    return ret

  @blocking
  def write( s, addr, data ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.req_class( XcelMsgType.WRITE, addr, data ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    s.entry = None

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, req_class, resp_class ):
    s.entry = None # store response

    s.req_class  = req_class
    s.resp_class = resp_class

    s.left  = XcelMinionIfcFL( s.read, s.write )
    s.right = XcelMasterIfcCL( req_class, resp_class, s.recv, s.recv_rdy )

    s.add_constraints(
      M( s.left.read  ) == M( s.right.req ),
      M( s.left.write ) == M( s.right.req ),
    )
