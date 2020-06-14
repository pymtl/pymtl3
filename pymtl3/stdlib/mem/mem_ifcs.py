"""
#=========================================================================
# MemIfcs
#=========================================================================
#
# Author: Shunning Jiang
# Date  : May 18, 2019
"""
from greenlet import greenlet

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.ifcs import MasterIfcCL, MasterIfcRTL, MinionIfcCL, MinionIfcRTL

from .MemMsg import MemMsgType, mk_mem_msg


class MemMasterIfcFL( Interface ):
  def construct( s, ReqType=None, RespType=None ):
    s.read  = CallerIfcFL()
    s.write = CallerIfcFL()
    s.amo   = CallerIfcFL()

  def __str__( s ):
    return f"r{s.read}|w{s.write}|a{s.amo}"

  def connect( s, other, parent ):
    if isinstance( other, MemMinionIfcCL ):
      m = MemIfcFL2CLAdapter( other.ReqType, other.RespType )

      if hasattr( parent, "MemIfcFL2CL_count" ):
        count = parent.MemIfcFL2CL_count
        setattr( parent, "MemIfcFL2CL_" + str( count ), m )
      else:
        parent.MemIfcFL2CL_count = 0
        parent.MemIfcFL2CL_0 = m

      connect_pairs(
        s,       m.left,
        m.right, other,
      )
      parent.MemIfcFL2CL_count += 1
      return True

    elif isinstance( other, MemMinionIfcRTL ):
      m = MemIfcFL2RTLAdapter( other.ReqType, other.RespType )

      if hasattr( parent, "MemIfcFL2RTL_count" ):
        count = parent.MemIfcFL2RTL_count
        setattr( parent, "MemIfcFL2RTL_" + str( count ), m )
      else:
        parent.MemIfcFL2RTL_count = 0
        parent.MemIfcFL2RTL_0 = m

      connect_pairs(
        s,       m.left,
        m.right, other,
      )
      parent.MemIfcFL2RTL_count += 1
      return True

    return False

class MemMinionIfcFL( Interface ):
  def construct( s, read=None, write=None, amo=None ):
    s.read  = CalleeIfcFL( method=read )
    s.write = CalleeIfcFL( method=write )
    s.amo   = CalleeIfcFL( method=amo )

  def __str__( s ):
    return f"r{s.read}|w{s.write}|a{s.amo}"

  def connect( s, other, parent ):
    if isinstance( other, MemMasterIfcCL ):
      m = MemIfcCL2FLAdapter( other.ReqType, other.RespType )

      if hasattr( parent, "MemIfcCL2FL_count" ):
        count = parent.MemIfcCL2FL_count
        setattr( parent, "MemIfcCL2FL_" + str( count ), m )
      else:
        parent.MemIfcCL2FL_count = 0
        parent.MemIfcCL2FL_0 = m

      connect_pairs(
        other,   m.left,
        m.right, other,
      )
      parent.MemIfcCL2FL_count += 1
      return True

    elif isinstance( other, MemMasterIfcRTL ):
      m = MemIfcRTL2FLAdapter( other.ReqType, other.RespType )

      if hasattr( parent, "MemIfcRTL2FL_count" ):
        count = parent.MemIfcRTL2FL_count
        setattr( parent, "MemIfcRTL2FL_" + str( count ), m )
      else:
        parent.MemIfcRTL2FL_count = 0
        parent.MemIfcRTL2FL_0 = m

      connect_pairs(
        other,   m.left,
        m.right, s,
      )
      parent.MemIfcRTL2FL_count += 1
      return True

    return False

class MemMasterIfcCL( MasterIfcCL ): pass

class MemMinionIfcCL( MinionIfcCL ): pass

class MemMasterIfcRTL( MasterIfcRTL ): pass

class MemMinionIfcRTL( MinionIfcRTL ): pass

class MemIfcCL2FLAdapter( Component ):

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, ReqType, RespType ):
    s.left  = MemMinionIfcCL( ReqType, RespType, s.recv, s.recv_rdy )
    s.right = MemMasterIfcFL()
    s.entry = None

    @update_once
    def up_memifc_cl_fl_blk():

      if s.entry is not None and s.left.resp.rdy():

        # Dequeue memory request message

        req     = s.entry
        s.entry = None

        len_ = int(req.len)
        if not len_: len_ = ReqType.data_nbits >> 3

        if   req.type_ == MemMsgType.READ:
          resp = RespType( req.type_, req.opaque, 0, req.len,
                             s.right.read( req.addr, len_ ) )

        elif req.type_ == MemMsgType.WRITE:
          s.right.write( req.addr, len_, req.data )
          # FIXME do we really set len=0 in response when doing subword wr?
          # resp = RespTypees( req.type_, req.opaque, 0, req.len, 0 )
          resp = RespType( req.type_, req.opaque, 0, 0, 0 )

        else: # AMOS
          resp = RespType( req.type_, req.opaque, 0, req.len,
             s.right.amo( req.type_, req.addr, len_, req.data ) )

        # Make line trace look better since s.right might get blocked
        assert s.left.resp.rdy()
        s.left.resp( resp )

    s.add_constraints(
      M(s.left.req) < U(up_memifc_cl_fl_blk), # bypass behavior
    )

class MemIfcFL2CLAdapter( Component ):

  def read( s, addr, nbytes ):

    # TODO refactor this greenlet stuff into some utility API
    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.create_req( MemMsgType.READ, 0, addr, nbytes ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.entry.data[0:nbytes<<3]
    s.entry = None
    return ret

  def write( s, addr, nbytes, data ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.create_req( MemMsgType.WRITE, 0, addr, nbytes, data ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    s.entry = None

  def amo( s, amo, addr, nbytes, data ):

    while not s.right.req.rdy():
      greenlet.getcurrent().parent.switch(0)

    s.right.req( s.create_req( amo, 0, addr, nbytes, data ) )

    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.entry.data
    s.entry = None
    return ret

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, ReqType, RespType ):
    s.entry = None # store response

    s.ReqType  = ReqType
    s.RespType = RespType

    Tlen  = ReqType.get_field_type('len')
    Tdata = ReqType.get_field_type('data')
    # Use create_req to handle type mismatch
    s.create_req = lambda a,b,c,d,e=0: ReqType( a, b, c, Tlen(d, trunc_int=True), Tdata(int(e)) )

    s.left  = MemMinionIfcFL( read=s.read, write=s.write, amo=s.amo )
    s.right = MemMasterIfcCL( ReqType, RespType, s.recv, s.recv_rdy )

    s.add_constraints(
      M(s.left.read)  == M(s.right.req),
      M(s.left.write) == M(s.right.req),
      M(s.left.amo)   == M(s.right.req),
      M(s.left.read)  >  M(s.right.resp), # Comb behavior
      M(s.left.write) >  M(s.right.resp), # Comb behavior
      M(s.left.amo)   >  M(s.right.resp), # Comb behavior
    )

#-------------------------------------------------------------------------
# RTL/FL adapters
#-------------------------------------------------------------------------

class MemIfcRTL2FLAdapter( Component ):

  def construct( s, ReqType, RespType ):
    s.left  = MemMinionIfcRTL( ReqType, RespType )
    s.right = MemMasterIfcFL()

    @update_once
    def up_memifc_rtl_fl_blk():

      if s.left.req.en and s.left.resp.rdy:

        if s.left.req.msg.type_ == MemMsgType.READ:
          resp = RespType( s.left.req.msg.type_, s.right.read( s.left.req.msg.addr ) )

        elif s.left.req.msg.type_ == MemMsgType.WRITE:
          s.right.write( s.left.req.msg.addr, s.left.req.msg.data )
          resp = RespType( s.left.req.msg.type_, 0 )

        else: # AMOs
          resp = RespType( req.type_, req.opaque, 0, req.len,
             s.right.amo( req.type_, req.addr, len_, req.data ) )

        s.left.resp.en  = Bits1(1)
        s.left.resp.msg = resp

    @update
    def up_memifc_rtl_fl_rdy():
      s.left.req.rdy = s.left.resp.rdy

class MemIfcFL2RTLAdapter( Component ):

  def construct( s, ReqType, RespType ):
    s.left  = MemMinionIfcFL ()
    s.right = MemMasterIfcRTL( ReqType, RespType )

    s.fl2cl       = MemIfcFL2CLAdapter( ReqType, RespType )
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
