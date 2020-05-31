"""
==========================================================================
 master_minion_ifc.py
==========================================================================
Master/minion send/recv interface implementations at CL and RTL.
 Author: Shunning Jiang
   Date: Jan 28, 2020
"""
from pymtl3 import *

from .send_recv_ifcs import RecvIfcRTL, SendIfcRTL

#-------------------------------------------------------------------------
# CL interfaces
#-------------------------------------------------------------------------

# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc.

class MasterIfcCL( Interface ):
  def construct( s, ReqType, RespType, resp=None, resp_rdy=None ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = CallerIfcCL( Type=ReqType )
    s.resp = CalleeIfcCL( Type=RespType, method=resp, rdy=resp_rdy )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class MinionIfcCL( Interface ):
  def construct( s, ReqType, RespType, req=None, req_rdy=None ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = CalleeIfcCL( Type=ReqType, method=req, rdy=req_rdy )
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
    s.req  = SendIfcRTL( Type=ReqType )
    s.resp = RecvIfcRTL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class MinionIfcRTL( Interface ):
  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = RecvIfcRTL( Type=ReqType )
    s.resp = SendIfcRTL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"
