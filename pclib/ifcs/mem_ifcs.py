#=========================================================================
# MemIfcs
#=========================================================================
#
# Author: Shunning Jiang
# Date  : May 8, 2019

from pymtl      import *

from .MemMsg import MemMsgType, mk_mem_msg
from .GuardedIfc import guarded_ifc, GuardedCallerIfc, GuardedCalleeIfc

class MemMasterIfcCL( Interface ):
  def construct( s, req_class, resp_class, resp=None, resp_rdy=None ):
    s.req_class  = req_class
    s.resp_class = resp_class
    s.req  = GuardedCallerIfc()
    s.resp = GuardedCalleeIfc( resp, resp_rdy )

  def connect( s, other, parent ):
    if isinstance( other, MemMinionIfcFL ):
      m = MemIfcCL2FLAdapter( s.req_class, s.resp_class )

      if hasattr( parent, "MemIfcCL2FL_count" ):
        count = parent.MemIfcCL2FL_count
        setattr( parent, "MemIfcCL2FL_" + str( count ), m )
      else:
        parent.MemIfcCL2FL_count = 0
        parent.MemIfcCL2FL_0 = m

      parent.connect_pairs(
        s,       m.left,
        m.right, other,
      )
      parent.MemIfcCL2FL_count += 1
      return True
    elif isinstance( other, MemMinionIfcCL ):
      assert s.req_class is other.req_class and s.resp_class is other.resp_class
      return False # use the default connect-by-name method

    return False

class MemMinionIfcCL( Interface ):
  def construct( s, req_class, resp_class, req=None, req_rdy=None ):
    s.req_class  = req_class
    s.resp_class = resp_class
    s.req  = GuardedCalleeIfc( req, req_rdy )
    s.resp = GuardedCallerIfc()

class MemMasterIfcFL( Interface ):
  def construct( s ):
    s.read  = CallerPort()
    s.write = CallerPort()
    s.amo   = CallerPort()

class MemMinionIfcFL( Interface ):
  def construct( s, read, write, amo ):
    s.read  = CalleePort( read )
    s.write = CalleePort( write )
    s.amo   = CalleePort( amo )

class MemIfcCL2FLAdapter( Component ):

  def recv_rdy( s ):
    return s.entry is None

  def recv( s, msg ):
    assert s.entry is None
    s.entry = msg

  def construct( s, req_class, resp_class ):
    s.left  = MemMinionIfcCL( req_class, resp_class, s.recv, s.recv_rdy )
    s.right = MemMasterIfcFL()
    s.entry = None

    @s.update
    def up_memifc_cl_fl_blk():

      if s.entry is not None and s.left.resp.rdy():

        # Dequeue memory request message

        req     = s.entry
        s.entry = None

        len_ = int(req.len)
        if not len_: len_ = req_classes[i].data_nbits >> 3

        if   req.type_ == MemMsgType.READ:
          resp = resp_class( req.type_, req.opaque, 0, req.len,
                             s.right.read( req.addr, len_ ) )

        elif req.type_ == MemMsgType.WRITE:
          s.right.write( req.addr, len_, req.data )
          # FIXME do we really set len=0 in response when doing subword wr?
          # resp = resp_classes( req.type_, req.opaque, 0, req.len, 0 )
          resp = resp_class( req.type_, req.opaque, 0, 0, 0 )

        else: # AMOS
          resp = resp_class( req.type_, req.opaque, 0, req.len,
             s.right.amo( req.type_, req.addr, len_, req.data ) )

        s.left.resp( resp )

    s.add_constraints(
      M(s.left.req) < U(up_memifc_cl_fl_blk), # bypass behavior
    )
