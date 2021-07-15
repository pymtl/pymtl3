"""
==========================================================================
 master_minion_ifc.py
==========================================================================
Master/minion send/recv interface implementations at CL and RTL.
 Author: Shunning Jiang
   Date: Jan 28, 2020
"""
from pymtl3 import *

from .ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.extra import clone_deepcopy

#-------------------------------------------------------------------------
# CL interfaces
#-------------------------------------------------------------------------

# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc.

class MasterIfcCL( Interface ):
  def construct( s, ReqType, RespType, *, req=None, req_rdy=None, resp=None, resp_rdy=None ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = CalleeIfcCL( Type=ReqType,  method=req, rdy=req_rdy )
    s.resp = CalleeIfcCL( Type=RespType, method=resp, rdy=resp_rdy )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class MinionIfcCL( Interface ):
  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = CallerIfcCL( Type=ReqType )
    s.resp = CallerIfcCL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

#-------------------------------------------------------------------------
# RTL interfaces
#-------------------------------------------------------------------------
# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc.

class MasterIfcRTL( Interface ):
  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = RecvIfcRTL( Type=ReqType )
    s.resp = SendIfcRTL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

  def connect( s, other, parent ):
    if isinstance( other, MinionIfcCL ):
      m = ValRdyMasterMinionRTL2CLAdapter( other.ReqType, other.RespType )

      if hasattr( parent, "ValRdyMasterMinionRTL2CLAdapter_count" ):
        count = parent.XcelIfcFL2RTL_count
        setattr( parent, "ValRdyMasterMinionRTL2CLAdapter_count" + str( count ), m )
      else:
        parent.ValRdyMasterMinionRTL2CLAdapter_count = 0
        parent.ValRdyMasterMinionRTL2CLAdapter_0 = m

      s       //= m.left
      m.right //= other
      parent.ValRdyMasterMinionRTL2CLAdapter_count += 1
      return True

    return False

class MinionIfcRTL( Interface ):
  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = RecvIfcRTL( Type=ReqType )
    s.resp = SendIfcRTL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class ValRdyMasterMinionRTL2CLAdapter( Component ):

  def req_rdy( s ):
    return s.req_entry is not None

  def req( s ):
    assert s.req_entry is not None
    ret = s.req_entry
    s.req_entry = None
    return ret

  def resp_rdy( s ):
    return s.resp_entry is None

  def resp( s, msg ):
    s.resp_entry = clone_deepcopy( msg )

  def construct( s, ReqType, RespType ):
    s.left  = MinionIfcRTL( ReqType, RespType )
    s.right = MasterIfcCL( ReqType, RespType, req=s.req, req_rdy=s.req_rdy, resp=s.resp, resp_rdy=s.resp_rdy )

    # Req side

    s.req_entry = None

    @update_ff
    def up_left_req_rdy():
      s.left.req.rdy <<= (s.req_entry is None)

    @update_once
    def up_left_req_msg():
      if s.req_entry is None:
        if s.left.req.val:
          s.req_entry = clone_deepcopy( s.left.req.msg )

    s.add_constraints(
      U( up_left_req_msg ) < M( s.req ),
      U( up_left_req_msg ) < M( s.req_rdy ),
    )

    # Resp side

    s.resp_entry = None
    s.resp_sent  = Wire()

    @update_once
    def up_right_resp():
      if s.resp_entry is None:
        s.left.resp.val @= 0
      else:
        s.left.resp.val @= 1
        s.left.resp.msg @= s.resp_entry

    @update_ff
    def up_resp_sent():
      s.resp_sent <<= s.left.resp.val & s.left.resp.rdy

    @update_once
    def up_clear():
      if s.resp_sent: # constraints reverse this
        s.resp_entry = None

    s.add_constraints(
      U( up_clear )   < M( s.resp ),
      U( up_clear )   < M( s.resp_rdy ),
      M( s.resp )     < U( up_right_resp ),
      M( s.resp_rdy ) < U( up_right_resp )
    )
